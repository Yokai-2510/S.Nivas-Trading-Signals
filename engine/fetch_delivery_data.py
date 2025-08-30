# --- engine/fetch_delivery_data.py ---

import pandas as pd
from datetime import datetime, timedelta
from nse import NSE
import tempfile
import shutil
from pathlib import Path

def get_latest_delivery_report(days_to_check=7, log_func=print):
    """
    Finds the most recent day with an available delivery report, downloads it,
    processes it, and returns the data as a DataFrame.

    Args:
        days_to_check (int): How many past days to check for a report.
        log_func (function): The logging function from the main engine.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        log_func(f"INFO: Using temporary directory for downloads: {temp_dir}", 'INFO')
        nse = NSE(download_folder=temp_dir)

        for i in range(days_to_check):
            target_date = datetime.now() - timedelta(days=i)
            
            if target_date.weekday() >= 5: # Skip weekends
                continue

            date_str = target_date.strftime("%d-%b-%Y")
            log_func(f"  ...Attempting to fetch delivery report for: {date_str}", 'INFO')
            
            try:
                # STEP 1: Download ONLY the required delivery report file.
                delivery_filepath = nse.deliveryBhavcopy(target_date)
                log_func(f"  ...Successfully downloaded: {delivery_filepath.name}", 'SUCCESS')
                
                # STEP 2: Process this single file.
                df = pd.read_csv(delivery_filepath)
                
                # CRITICAL: The column names from NSE have leading spaces.
                equity_series = [' EQ', ' BE', ' BZ', ' SM', ' ST']
                df = df[df[' SERIES'].isin(equity_series)].copy()
                
                if df.empty:
                    log_func(f"WARNING: No equity series data found in report for {date_str}.", 'WARNING')
                    continue

                # Data Cleaning and Type Conversion
                df[' DELIV_QTY'] = pd.to_numeric(df[' DELIV_QTY'], errors='coerce').fillna(0).astype(int)
                df[' TTL_TRD_QNTY'] = pd.to_numeric(df[' TTL_TRD_QNTY'], errors='coerce').fillna(0).astype(int)

                # Special Logic: For 'BE' and 'BZ' series, all trades are delivery-based.
                is_be_bz = df[' SERIES'].isin([' BE', ' BZ'])
                df.loc[is_be_bz, ' DELIV_QTY'] = df.loc[is_be_bz, ' TTL_TRD_QNTY']
                
                # Calculate Delivery Percentage
                df['Delivery_Perc'] = 0.0
                traded_mask = df[' TTL_TRD_QNTY'] > 0
                df.loc[traded_mask, 'Delivery_Perc'] = round(
                    (df.loc[traded_mask, ' DELIV_QTY'] / df.loc[traded_mask, ' TTL_TRD_QNTY']) * 100, 2
                )

                # Final Cleanup and Column Selection
                final_df = df[['SYMBOL', 'Delivery_Perc']].rename(columns={'SYMBOL': 'Symbol'})
                final_df.attrs['date'] = target_date.strftime('%Y-%m-%d')
                
                return final_df

            except RuntimeError:
                log_func(f"WARNING: Report for {date_str} not available. Trying previous day.", 'WARNING')
                continue
            except Exception as e:
                log_func(f"ERROR: Unexpected error for {date_str}: {e}", 'ERROR')
                continue

    finally:
        log_func(f"INFO: Cleaning up temporary directory: {temp_dir}", 'INFO')
        shutil.rmtree(temp_dir)

    log_func(f"ERROR: Failed to fetch any delivery report within the last {days_to_check} days.", 'ERROR')
    return pd.DataFrame()