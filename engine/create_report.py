# --- engine/create_report.py ---
import pandas as pd
import os
from datetime import datetime

def save_to_excel(reports_dict, config, log_func):
    if not reports_dict:
        log_func("INFO: No reports in memory to save.", 'INFO')
        return True

    output_dir = config['file_paths']['output_dir']
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    excel_format = config['export_settings'].get('excel_format', 'Individual File per Analysis')

    try:
        if excel_format == 'Single File with Multiple Sheets':
            filename = f"{today_str}_Analysis_Report.xlsx"
            filepath = os.path.join(output_dir, filename)
            log_func(f"INFO: Saving all reports to a single file: {filepath}", 'INFO')
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for report_name, df in reports_dict.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=report_name, index=False)
            log_func(f"SUCCESS: All reports saved to '{filepath}'.", 'SUCCESS')
        
        else: # Default to Individual File per Analysis
            log_func("INFO: Saving each report to an individual Excel file.", 'INFO')
            for report_name, df in reports_dict.items():
                if df.empty:
                    log_func(f"INFO: DataFrame for '{report_name}' is empty. Skipping file save.", 'INFO')
                    continue
                filename = f"{today_str}_{report_name}.xlsx"
                filepath = os.path.join(output_dir, filename)
                log_func(f"INFO: Saving report for '{report_name}' to: {filepath}", 'INFO')
                df.to_excel(filepath, index=False, sheet_name='Results')
                log_func(f"SUCCESS: Wrote {len(df)} rows to '{filepath}'.", 'SUCCESS')
        return True
    
    except Exception as e:
        log_func(f"ERROR: Failed to save to Excel. Error: {e}", 'ERROR')
        return False