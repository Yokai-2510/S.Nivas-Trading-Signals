# --- fetch_data.py ---

import pandas as pd
import yfinance as yf
import requests
import os
import gzip
import json
from io import StringIO, BytesIO
import sys # Required for redirecting stdout

def _fetch_tickers_nifty500(filepath, config, log_func):
    log_func("INFO: Fetching fresh Nifty 500 Ticker List from NSE...", 'INFO')
    url = config['data_urls']['nifty500_tickers_url']
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        symbols = (df['Symbol'].astype(str) + '.NS').tolist()
        final_df = pd.DataFrame(sorted(list(set(symbols))), columns=['Symbol'])
        final_df.to_csv(filepath, index=False)
        log_func(f"SUCCESS: Saved {len(final_df)} Nifty 500 tickers to '{filepath}'.", 'SUCCESS')
        return final_df['Symbol'].tolist()
    except Exception as e:
        log_func(f"ERROR: Failed to fetch Nifty 500 tickers: {e}", 'ERROR')
        return []

def _fetch_tickers_fno(filepath, config, log_func):
    log_func("INFO: Fetching F&O instrument list from Upstox...", 'INFO')
    url = config['data_urls']['fno_tickers_url']
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz_file:
            instrument_data = json.loads(gz_file.read().decode('utf-8'))
        unique_fno_symbols = {inst.get('underlying_symbol') for inst in instrument_data if isinstance(inst, dict) and inst.get('segment') == 'NSE_FO' and inst.get('underlying_symbol')}
        if not unique_fno_symbols:
            log_func("WARNING: No F&O symbols found in Upstox data.", 'WARNING')
            return []
        final_symbols = [f"{s}.NS" for s in sorted(list(unique_fno_symbols))]
        output_df = pd.DataFrame(final_symbols, columns=['Symbol'])
        output_df.to_csv(filepath, index=False)
        log_func(f"SUCCESS: Saved {len(output_df)} unique F&O tickers to '{filepath}'.", 'SUCCESS')
        return output_df['Symbol'].tolist()
    except Exception as e:
        log_func(f"ERROR: Failed to fetch F&O tickers: {e}", 'ERROR')
        return []

def _fetch_ohlcv(tickers, filepath, dataset_name, period, interval, log_func):
    if not tickers:
        log_func(f"WARNING: Ticker list for {dataset_name} is empty. Skipping OHLCV download.", 'WARNING')
        pd.DataFrame().to_csv(filepath)
        return
    
    log_func(f"INFO: Fetching OHLCV for {len(tickers)} {dataset_name} stocks...", 'INFO')
    
    # --- THIS IS THE ROBUST SOLUTION ---
    # 1. Create an in-memory text buffer to act as a temporary console.
    temp_stdout = StringIO()
    original_stdout = sys.stdout
    
    try:
        # 2. Redirect the system's standard output to our in-memory buffer.
        sys.stdout = temp_stdout
        
        # 3. Run the yfinance download. Any prints (progress, errors) will be captured by our buffer.
        #    'progress=False' is still used to keep the captured output clean.
        data = yf.download(tickers=tickers, period=period, interval=interval, auto_adjust=True, threads=True, progress=False)
        
    except Exception as e:
        # Catch any unexpected critical errors during the download itself.
        log_func(f"CRITICAL ERROR during {dataset_name} OHLCV download: {e}", 'ERROR')
        data = pd.DataFrame() # Ensure data is an empty DataFrame on critical failure
    finally:
        # 4. CRITICAL: Always restore the original standard output, no matter what happens.
        sys.stdout = original_stdout

    # 5. Get the captured text and check for non-critical download failures.
    captured_output = temp_stdout.getvalue()
    if "Failed download" in captured_output:
        # Extract and log only the relevant error lines.
        error_lines = [line for line in captured_output.split('\n') if "Failed download" in line]
        for error in error_lines:
            log_func(f"WARNING: yfinance issue: {error.strip()}", 'WARNING')

    # 6. Proceed with saving the data that was successfully downloaded.
    try:
        if data.empty:
            log_func(f"ERROR: yfinance returned no data for {dataset_name}. Check logs for warnings.", 'ERROR')
            # Create an empty file to prevent future loading errors
            pd.DataFrame().to_csv(filepath)
        else:
            data.dropna(axis=0, how='all', inplace=True)
            data.to_csv(filepath)
            log_func(f"SUCCESS: {dataset_name} OHLCV data saved to '{filepath}'.", 'SUCCESS')
    except Exception as e:
        log_func(f"ERROR: An error occurred while saving {dataset_name} data: {e}", 'ERROR')


def prepare_market_data(config, log_func):
    data_cfg = config['data_settings']
    path_cfg = config['file_paths']
    
    # Ensure the parent directory of the files exists
    first_file_path = next(iter(path_cfg.values()))
    os.makedirs(os.path.dirname(first_file_path), exist_ok=True)

    n500_tickers = []
    if data_cfg['n500_fetch_tickers']:
        n500_tickers = _fetch_tickers_nifty500(path_cfg['n500_tickers_file'], config, log_func)
    else:
        log_func(f"INFO: Using existing Nifty 500 ticker file.", 'INFO')
        try:
            n500_tickers = pd.read_csv(path_cfg['n500_tickers_file'])['Symbol'].tolist()
        except FileNotFoundError:
            log_func(f"ERROR: Nifty 500 ticker file not found at '{path_cfg['n500_tickers_file']}'. Please enable download.", 'ERROR')
    
    fno_tickers = []
    if data_cfg['fno_fetch_tickers']:
        fno_tickers = _fetch_tickers_fno(path_cfg['fno_tickers_file'], config, log_func)
    else:
        log_func(f"INFO: Using existing F&O ticker file.", 'INFO')
        try:
            fno_tickers = pd.read_csv(path_cfg['fno_tickers_file'])['Symbol'].tolist()
        except FileNotFoundError:
            log_func(f"ERROR: F&O ticker file not found at '{path_cfg['fno_tickers_file']}'. Please enable download.", 'ERROR')

    log_func("\n--- Fetching OHLCV Data ---", 'HEADER')
    if data_cfg['n500_fetch_ohlcv']:
        _fetch_ohlcv(n500_tickers, path_cfg['n500_ohlcv_file'], "Nifty 500", data_cfg['history_period'], data_cfg['data_interval'], log_func)
    else:
        log_func("INFO: Skipping Nifty 500 OHLCV download as per config.", 'INFO')

    if data_cfg['fno_fetch_ohlcv']:
        _fetch_ohlcv(fno_tickers, path_cfg['fno_ohlcv_file'], "F&O", data_cfg['history_period'], data_cfg['data_interval'], log_func)
    else:
        log_func("INFO: Skipping F&O OHLCV download as per config.", 'INFO')
    
    return (n500_tickers, fno_tickers)
