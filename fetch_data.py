import pandas as pd
import yfinance as yf
import requests
import os
import gzip
import json
from io import StringIO, BytesIO

def _fetch_tickers_nifty500(filepath, config, log_func): # Downloads Nifty 500 tickers from NSE
    log_func("INFO: Fetching fresh Nifty 500 Ticker List from NSE...", 'INFO')
    url = config['data_urls']['nifty500_tickers_url']
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status() # Check for request errors
        
        df = pd.read_csv(StringIO(response.text)) # Read CSV data from memory
        symbols = (df['Symbol'].astype(str) + '.NS').tolist() # Add .NS suffix
        final_df = pd.DataFrame(sorted(list(set(symbols))), columns=['Symbol']) # Ensure uniqueness and sort
        
        final_df.to_csv(filepath, index=False) # Save to file
        log_func(f"SUCCESS: Saved {len(final_df)} Nifty 500 tickers to '{filepath}'.", 'SUCCESS')
        return final_df['Symbol'].tolist()
    except Exception as e:
        log_func(f"ERROR: Failed to fetch Nifty 500 tickers: {e}", 'ERROR')
        return []

def _fetch_tickers_fno(filepath, config, log_func): # Downloads F&O tickers from Upstox
    log_func("INFO: Fetching F&O instrument list from Upstox...", 'INFO')
    url = config['data_urls']['fno_tickers_url']
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status() # Check for request errors
        
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz_file: # Decompress GZIP in memory
            instrument_data = json.loads(gz_file.read().decode('utf-8'))
        
        # Filter for unique underlying F&O stock symbols
        unique_fno_symbols = {inst.get('underlying_symbol') for inst in instrument_data if isinstance(inst, dict) and inst.get('segment') == 'NSE_FO' and inst.get('underlying_symbol')}
        if not unique_fno_symbols:
            log_func("WARNING: No F&O symbols found in Upstox data.", 'WARNING')
            return []

        final_symbols = [f"{s}.NS" for s in sorted(list(unique_fno_symbols))] # Add .NS suffix and sort
        output_df = pd.DataFrame(final_symbols, columns=['Symbol'])
        output_df.to_csv(filepath, index=False) # Save to file
        
        log_func(f"SUCCESS: Saved {len(output_df)} unique F&O tickers to '{filepath}'.", 'SUCCESS')
        return output_df['Symbol'].tolist()
    except Exception as e:
        log_func(f"ERROR: Failed to fetch F&O tickers: {e}", 'ERROR')
        return []

def _fetch_ohlcv(tickers, filepath, dataset_name, period, interval, log_func): # Downloads OHLCV data using yfinance
    if not tickers:
        log_func(f"WARNING: Ticker list for {dataset_name} is empty. Skipping OHLCV download.", 'WARNING')
        pd.DataFrame().to_csv(filepath) # Create empty file to prevent errors
        return
    
    log_func(f"INFO: Fetching OHLCV for {len(tickers)} {dataset_name} stocks...", 'INFO')
    try:
        data = yf.download(tickers=tickers, period=period, interval=interval, auto_adjust=True, threads=True)
        if data.empty:
            log_func(f"ERROR: yfinance returned no data for {dataset_name}.", 'ERROR')
        data.dropna(axis=0, how='all', inplace=True) # Drop rows where all values are NaN
        data.to_csv(filepath)
        log_func(f"SUCCESS: {dataset_name} OHLCV data saved to '{filepath}'.", 'SUCCESS')
    except Exception as e:
        log_func(f"ERROR: An error occurred during {dataset_name} OHLCV download: {e}", 'ERROR')

def prepare_market_data(config, log_func): # Main orchestrator for data preparation
    data_cfg = config['data_settings']
    path_cfg = config['file_paths']
    os.makedirs(path_cfg['output_dir'], exist_ok=True) # Ensure source directory exists

    # --- Nifty 500 Tickers ---
    n500_tickers = []
    if data_cfg['n500_fetch_tickers']:
        n500_tickers = _fetch_tickers_nifty500(path_cfg['n500_tickers_file'], config, log_func)
    else:
        log_func(f"INFO: Using existing Nifty 500 ticker file.", 'INFO')
        try:
            n500_tickers = pd.read_csv(path_cfg['n500_tickers_file'])['Symbol'].tolist()
        except FileNotFoundError:
            log_func(f"ERROR: Nifty 500 ticker file not found. Please enable download.", 'ERROR')
    
    # --- F&O Tickers ---
    fno_tickers = []
    if data_cfg['fno_fetch_tickers']:
        fno_tickers = _fetch_tickers_fno(path_cfg['fno_tickers_file'], config, log_func)
    else:
        log_func(f"INFO: Using existing F&O ticker file.", 'INFO')
        try:
            fno_tickers = pd.read_csv(path_cfg['fno_tickers_file'])['Symbol'].tolist()
        except FileNotFoundError:
            log_func(f"ERROR: F&O ticker file not found. Please enable download.", 'ERROR')

    # --- OHLCV Data ---
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