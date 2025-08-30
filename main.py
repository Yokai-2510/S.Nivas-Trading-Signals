# --- main.py ---

import threading
import os
import json
import pandas as pd
from datetime import datetime
from engine import fetch_data, indicators, format_dataset, create_report, fetch_delivery_data

class Engine:
    def __init__(self, app_path, log_callback, progress_callback):
        self.app_path = app_path
        self.log = log_callback
        self.update_progress = progress_callback
        self.stop_event = threading.Event()
        self.config = self._load_config()
        self.analysis_reports = {}

    def _load_config(self):
        config_path = os.path.join(self.app_path, "source", "config.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.log(f"ERROR: config.json invalid or not found at '{config_path}': {e}", "ERROR")
            return {}

    def start_data_fetch_in_thread(self, gui_config):
        self.config = gui_config; self.stop_event.clear()
        threading.Thread(target=self._run_data_fetch_flow, daemon=True).start()

    def start_analysis_in_thread(self, gui_config, analysis_tasks):
        self.config = gui_config; self.stop_event.clear()
        self.analysis_reports.clear()
        threading.Thread(target=self._run_analysis_flow, args=(analysis_tasks,), daemon=True).start()
        
    def start_export_in_thread(self, gui_config):
        self.config = gui_config; self.stop_event.clear()
        threading.Thread(target=self._run_export_flow, daemon=True).start()

    def stop_process(self):
        self.log("--- STOP-SIGNAL SENT ---", 'WARNING'); self.stop_event.set()

    def _run_data_fetch_flow(self):
        try:
            self.log("="*80 + "\n--- Running Data Fetch ---", 'HEADER')
            self.update_progress(0.1, "Starting data fetch...")
            # Ensure file paths in config are absolute for robustness
            for key, path in self.config['file_paths'].items():
                if not os.path.isabs(path):
                    self.config['file_paths'][key] = os.path.join(self.app_path, path)

            fetch_data.prepare_market_data(self.config, self.log)
        finally:
            self.log(f"--- Process Finished ---", "SUCCESS")
            self.update_progress(1.0, "Data Fetch Finished.")
            self.log("INTERNAL_STATE_UPDATE", "ANALYSIS_READY")

    def _run_analysis_flow(self, analysis_tasks):
        try:    
            self.log("\n" + "="*80 + "\n--- Running Analysis ---", 'HEADER'); self.update_progress(0.1, "Loading local data...")
            
            paths = self.config['file_paths']
            n500_tickers_path = os.path.join(self.app_path, paths['n500_tickers_file'])
            fno_tickers_path = os.path.join(self.app_path, paths['fno_tickers_file'])
            n500_ohlcv_path = os.path.join(self.app_path, paths['n500_ohlcv_file'])
            fno_ohlcv_path = os.path.join(self.app_path, paths['fno_ohlcv_file'])

            try:
                n500_tickers = pd.read_csv(n500_tickers_path)['Symbol'].tolist()
                fno_tickers = pd.read_csv(fno_tickers_path)['Symbol'].tolist()
                n500_ohlcv = pd.read_csv(n500_ohlcv_path, header=[0, 1], index_col=0, parse_dates=True)
                fno_ohlcv = pd.read_csv(fno_ohlcv_path, header=[0, 1], index_col=0, parse_dates=True)
            except FileNotFoundError as e: 
                self.log(f"ERROR: Could not load data file: {e}. Run 'Fetch Data' first.", "ERROR"); return

            self.log("INFO: Fetching latest NSE delivery percentage data...", "INFO")
            delivery_df = fetch_delivery_data.get_latest_delivery_report(log_func=self.log)
            if delivery_df.empty:
                self.log("WARNING: Could not fetch delivery data. The 'High Delivery' signal will be disabled.", "WARNING")
            else:
                self.log(f"SUCCESS: Fetched delivery data for {delivery_df.attrs.get('date', 'N/A')}. Found {len(delivery_df)} records.", "SUCCESS")
                delivery_df['Symbol'] = delivery_df['Symbol'] + '.NS'
                delivery_df.set_index('Symbol', inplace=True)
                
            for task_name in analysis_tasks: 
                if self.stop_event.is_set(): return
                self.log(f"\n--- Analyzing: {task_name} ---", "INFO")
                stock_list = n500_tickers if 'N500' in task_name else fno_tickers
                ohlcv_data = n500_ohlcv if 'N500' in task_name else fno_ohlcv
                analysis_type = 'Swing' if 'SWING' in task_name else 'Momentum'
                raw_results = []
                for i, symbol in enumerate(stock_list):
                    if self.stop_event.is_set(): break
                    if (i + 1) % 100 == 0: self.log(f"  ...processed {i+1}/{len(stock_list)} for {task_name}...")
                    try:
                        stock_df = ohlcv_data.loc[:, (slice(None), symbol)]; stock_df.columns = stock_df.columns.droplevel(1)
                        if stock_df.empty or stock_df.isnull().all().all(): continue
                    except KeyError: continue
                    
                    # --- MODIFIED LOGIC: Look up Delivery % for BOTH N500 and F&O stocks ---
                    delivery_perc = 0.0
                    if not delivery_df.empty and symbol in delivery_df.index:
                        delivery_perc = delivery_df.at[symbol, 'Delivery_Perc']
                    
                    # Pass the delivery percentage to the indicator function
                    enriched_df = indicators.add_all_indicators(
                        stock_df.reset_index(), 
                        self.config['swing_rules'], 
                        self.config['momentum_rules'],
                        delivery_perc=delivery_perc
                    )

                    if enriched_df is None or enriched_df.empty: continue
                    latest_row = enriched_df.iloc[-1]
                    signals = indicators.evaluate_swing_rules(latest_row, self.config['swing_rules']) if analysis_type == 'Swing' else indicators.evaluate_momentum_rules(latest_row, self.config['momentum_rules'])
                    for result in signals:
                        result.update({'TimeStamp': datetime.now().strftime("%Y-%m-%d %H:%M"), 'Stock': symbol.replace('.NS', '')})
                        raw_results.append(result)
                if not self.stop_event.is_set():
                    final_report_df = format_dataset.create_wide_report(raw_results, task_name)
                    self.analysis_reports[task_name] = final_report_df
                    self.log(f"SUCCESS: Analysis for {task_name} complete. Found {len(final_report_df)} potential signals.", "SUCCESS")
        finally:
            if self.stop_event.is_set():
                self.log(f"--- Process Stopped by User ---", "WARNING")
            else:
                self.log(f"--- Process Finished. Ready for Export. ---", "SUCCESS")
            self.update_progress(1.0, "Analysis Finished.")
            self.log("INTERNAL_STATE_UPDATE", "EXPORT_READY")
            
    def _run_export_flow(self):
        try:
            self.log("\n" + "="*80 + "\n--- Running Export ---", 'HEADER')
            if not self.analysis_reports:
                self.log("WARNING: No analysis results to export. Run analysis first.", "WARNING"); return
            
            output_dir = self.config['file_paths']['output_dir']
            if not os.path.isabs(output_dir):
                self.config['file_paths']['output_dir'] = os.path.join(self.app_path, output_dir)

            create_report.save_to_excel(self.analysis_reports, self.config, self.log)
        finally:
            self.log(f"--- Process Finished ---", "SUCCESS")
            self.update_progress(1.0, "Export Finished.")
            self.log("INTERNAL_STATE_UPDATE", "IDLE")
