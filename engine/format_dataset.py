import pandas as pd
from datetime import datetime

def create_wide_report(raw_results, analysis_name): # Converts the raw signal list into a final, wide-format DataFrame report
    if not raw_results: # Handle cases where no signals were generated
        print(f"INFO: No raw results found for '{analysis_name}'. Returning an empty report.")
        return pd.DataFrame()

    pivoted_records = []
    # Create a temporary DataFrame to easily group signals by stock
    long_df = pd.DataFrame(raw_results)
    
    for stock_name, group in long_df.groupby('Stock'):
        total_signals = len(group)
        signals_met = int(group['SignalBool'].sum()) # Count how many signals are True

        # Create the base record for the stock with summary information
        record = {
            'Timestamp': group['TimeStamp'].iloc[0],
            'Stock': stock_name,
            'TradeType': analysis_name,
            'All Signals Met': signals_met == total_signals,
            'Signals Score': f"{signals_met}/{total_signals}"
        }

        # Iterate through the signals for this stock and pivot them into wide-format columns
        for i, row in group.reset_index(drop=True).iterrows():
            # Use a consistent naming convention for the pivoted columns
            record[f'Indicator {i+1} - Name'] = row['Criteria']
            record[f'Indicator {i+1} - Status'] = 'TRUE' if row['SignalBool'] else 'FALSE'
            record[f'Indicator {i+1} - Threshold'] = row['ThresholdValue']
            record[f'Indicator {i+1} - Current'] = row['CurrentValue']
        
        pivoted_records.append(record)

    if not pivoted_records: # Final check in case grouping failed
        return pd.DataFrame()

    wide_df = pd.DataFrame(pivoted_records)
    
    # Create a temporary numeric sort key to handle scores like "10/10" vs "2/10" correctly
    try:
        wide_df['sort_key'] = wide_df['Signals Score'].apply(lambda x: int(x.split('/')[0]))
        # Sort by the highest score first, then alphabetically by stock name
        wide_df.sort_values(by=['sort_key', 'Stock'], ascending=[False, True], inplace=True)
        wide_df.drop(columns='sort_key', inplace=True) # Remove the temporary sort key
    except (ValueError, IndexError):
        # Fallback sort if 'Signals Score' format is unexpected
        wide_df.sort_values(by=['Stock'], ascending=True, inplace=True)

    return wide_df.reset_index(drop=True) # Return a clean, re-indexed DataFrame