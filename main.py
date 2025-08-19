# --- main.py ---

import threading
import os
import json
import pandas as pd
from datetime import datetime
from engine import fetch_data, indicators, format_dataset, create_report

class Engine:

    def __init__(self, log_callback, progress_callback):
        self.log = log_callback
        self.update_progress = progress_callback
        self.stop_event = threading.Event()
        self.config = self._load_config()
        self.analysis_reports = {}

    def _load_config(self):
        try:
            with open("source/config.json", "r") as f: return json.load(f)
        except Exception as e: self.log(f"ERROR: config.json invalid: {e}", "ERROR"); return {}

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
            fetch_data.prepare_market_data(self.config, self.log)
        finally:
            self.log(f"--- Process Finished ---", "SUCCESS")
            self.update_progress(1.0, "Data Fetch Finished.")
            self.log("INTERNAL_STATE_UPDATE", "ANALYSIS_READY")


    def _run_analysis_flow(self, analysis_tasks):

        try:    
            self.log("\n" + "="*80 + "\n--- Running Analysis ---", 'HEADER'); self.update_progress(0.1, "Loading local data...")
            try:
                n500_tickers = pd.read_csv(self.config['file_paths']['n500_tickers_file'])['Symbol'].tolist()
                fno_tickers = pd.read_csv(self.config['file_paths']['fno_tickers_file'])['Symbol'].tolist()
                n500_ohlcv = pd.read_csv(self.config['file_paths']['n500_ohlcv_file'], header=[0, 1], index_col=0, parse_dates=True)
                fno_ohlcv = pd.read_csv(self.config['file_paths']['fno_ohlcv_file'], header=[0, 1], index_col=0, parse_dates=True)
            except FileNotFoundError as e: self.log(f"ERROR: Could not load data file: {e}. Run 'Fetch Data' first.", "ERROR"); return
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
                    enriched_df = indicators.add_all_indicators(stock_df.reset_index(), self.config['swing_rules'], self.config['momentum_rules'])
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
            self.log(f"--- Process Finished. Ready for Export. ---", "SUCCESS")
            self.update_progress(1.0, "Analysis Finished.")
            self.log("INTERNAL_STATE_UPDATE", "EXPORT_READY")
            
            
    def _run_export_flow(self):
        try:
            self.log("\n" + "="*80 + "\n--- Running Export ---", 'HEADER')
            if not self.analysis_reports:
                self.log("WARNING: No analysis results to export. Run analysis first.", "WARNING"); return

            # Simplified export logic - only saves to Excel
            create_report.save_to_excel(self.analysis_reports, self.config, self.log)

        finally:
            self.log(f"--- Process Finished ---", "SUCCESS")
            self.update_progress(1.0, "Export Finished.")
            self.log("INTERNAL_STATE_UPDATE", "IDLE")