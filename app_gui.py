# --- app_gui.py (Final Polished UI) ---
import customtkinter as ctk
from tkinter import filedialog
import json
import os
from main import Engine

class AppGUI(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, corner_radius=0, fg_color="#242424") # Main background
        self.engine = engine
        self.config = engine.config

        # --- Main Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = self._create_sidebar()
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")

        # --- Content Frames ---
        self.dashboard_frame = self._create_dashboard_frame()
        self.config_frame = self._create_config_frame()
        self.logs_frame = self._create_logs_frame()

        # Show initial frame
        self._select_frame_by_name("dashboard")
        self.update_ui_state("IDLE")

    # --- Core App Logic ---
    def update_ui_state(self, state):
        is_idle = state in ["IDLE", "ANALYSIS_READY", "EXPORT_READY"]
        is_busy = state == "BUSY"
        
        self.fetch_button.configure(state="normal" if not is_busy else "disabled")
        self.run_button.configure(state="normal" if state in ["ANALYSIS_READY", "EXPORT_READY"] else "disabled")
        self.export_button.configure(state="normal" if state == "EXPORT_READY" else "disabled")
        self.stop_button.configure(state="normal" if is_busy else "disabled")
        if hasattr(self, 'save_config_button'):
            self.save_config_button.configure(state="normal" if is_idle else "disabled")

    def log(self, message, tag='DEFAULT'):
        if message == "INTERNAL_STATE_UPDATE": self.update_ui_state(tag); return
        self.log_textbox.configure(state="normal"); self.log_textbox.insert("end", f"{message}\n", tag); self.log_textbox.see("end"); self.log_textbox.configure(state="disabled")

    def fetch_data_button_pressed(self):
        self.update_ui_state("BUSY"); self.update_progress(0, "Starting data fetch...")
        self.engine.start_data_fetch_in_thread(self._get_current_config())
    
    def run_analysis_button_pressed(self):
        self.update_ui_state("BUSY"); self.update_progress(0, "Starting analysis...")
        tasks = {k for k, v in self.analysis_vars.items() if v.get()}
        self.engine.start_analysis_in_thread(self._get_current_config(), tasks)

    def export_button_pressed(self):
        self.update_ui_state("BUSY"); self.update_progress(0, "Starting export...")
        self.engine.start_export_in_thread(self._get_current_config())

    # --- Frame Creation & Switching ---
    def _select_frame_by_name(self, name):
        buttons = [self.dashboard_button, self.config_button, self.logs_button]
        frames = {
            "dashboard": self.dashboard_frame,
            "config": self.config_frame,
            "logs": self.logs_frame
        }
        
        for button in buttons:
            button.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        for frame in frames.values():
            frame.grid_forget()

        if name == "dashboard":
            self.dashboard_button.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
            self.dashboard_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif name == "config":
            self.config_button.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
            self.config_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif name == "logs":
            self.logs_button.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
            self.logs_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    
    def _create_sidebar(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#2b2b2b", width=200)
        frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(frame, text="Signal Engine", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        ctk.CTkLabel(frame, text="v1.1", font=ctk.CTkFont(size=12), text_color="gray60").grid(row=1, column=0, padx=20, pady=(0, 25), sticky="n")

        self.dashboard_button = ctk.CTkButton(frame, text="Dashboard", height=40, corner_radius=6, command=lambda: self._select_frame_by_name("dashboard"), font=ctk.CTkFont(size=14))
        self.dashboard_button.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        
        self.config_button = ctk.CTkButton(frame, text="Configuration", height=40, corner_radius=6, command=lambda: self._select_frame_by_name("config"), font=ctk.CTkFont(size=14))
        self.config_button.grid(row=3, column=0, padx=15, pady=8, sticky="ew")
        
        self.logs_button = ctk.CTkButton(frame, text="Logs", height=40, corner_radius=6, command=lambda: self._select_frame_by_name("logs"), font=ctk.CTkFont(size=14))
        self.logs_button.grid(row=4, column=0, padx=15, pady=8, sticky="ewn")

        return frame

    def _create_dashboard_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1) # Give more weight to analysis
        frame.grid_rowconfigure(2, weight=0) # Status frame has fixed size

        # --- Card 1: Data Preparation ---
        data_card = ctk.CTkFrame(frame, corner_radius=10, fg_color="#2b2b2b")
        data_card.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        data_card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(data_card, text="Step 1: Data Preparation", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        fetch_options_frame = ctk.CTkFrame(data_card, fg_color="transparent")
        fetch_options_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        fetch_options_frame.grid_columnconfigure((0, 1), weight=1)
        self.data_fetch_vars = {
            'n500_fetch_tickers': ctk.BooleanVar(value=self.config["data_settings"].get('n500_fetch_tickers', False)), 'n500_fetch_ohlcv': ctk.BooleanVar(value=self.config["data_settings"].get('n500_fetch_ohlcv', False)),
            'fno_fetch_tickers': ctk.BooleanVar(value=self.config["data_settings"].get('fno_fetch_tickers', False)), 'fno_fetch_ohlcv': ctk.BooleanVar(value=self.config["data_settings"].get('fno_fetch_ohlcv', False))
        }
        ctk.CTkCheckBox(fetch_options_frame, text="Nifty 500 Tickers", variable=self.data_fetch_vars['n500_fetch_tickers']).grid(row=0, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(fetch_options_frame, text="Nifty 500 OHLCV", variable=self.data_fetch_vars['n500_fetch_ohlcv']).grid(row=1, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(fetch_options_frame, text="F&O Tickers", variable=self.data_fetch_vars['fno_fetch_tickers']).grid(row=0, column=1, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(fetch_options_frame, text="F&O OHLCV", variable=self.data_fetch_vars['fno_fetch_ohlcv']).grid(row=1, column=1, padx=5, pady=6, sticky="w")

        self.fetch_button = ctk.CTkButton(data_card, text="FETCH LATEST DATA", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.fetch_data_button_pressed)
        self.fetch_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        # --- Card 2: Analysis & Reporting ---
        analysis_card = ctk.CTkFrame(frame, corner_radius=10, fg_color="#2b2b2b")
        analysis_card.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        analysis_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(analysis_card, text="Step 2: Analysis & Reporting", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        analysis_frame = ctk.CTkFrame(analysis_card, fg_color="transparent")
        analysis_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        analysis_frame.grid_columnconfigure((0, 1), weight=1)
        self.analysis_vars = {'N500_SWING': ctk.BooleanVar(value=True), 'N500_MOMENTUM': ctk.BooleanVar(value=True), 'FNO_SWING': ctk.BooleanVar(value=True), 'FNO_MOMENTUM': ctk.BooleanVar(value=True)}
        for i, (key, var) in enumerate(self.analysis_vars.items()): ctk.CTkCheckBox(analysis_frame, text=key.replace('_', ' - '), variable=var).grid(row=i//2, column=i%2, padx=5, pady=6, sticky="w")

        self.run_button = ctk.CTkButton(analysis_card, text="RUN ANALYSIS", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.run_analysis_button_pressed)
        self.run_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 10))
        
        self.export_button = ctk.CTkButton(analysis_card, text="EXPORT RESULTS", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.export_button_pressed)
        self.export_button.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- Card 3: Application Status ---
        status_card = ctk.CTkFrame(frame, corner_radius=10, fg_color="#2b2b2b")
        status_card.grid(row=2, column=0, sticky="nsew")
        status_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(status_card, text="Status:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=(20,10), pady=(15,5), sticky="w")
        self.status_label = ctk.CTkLabel(status_card, text="Idle", font=ctk.CTkFont(size=14), text_color="gray70"); self.status_label.grid(row=0, column=1, padx=0, pady=(15,5), sticky="w")
        self.progressbar = ctk.CTkProgressBar(status_card, progress_color="#4CAF50"); self.progressbar.grid(row=1, column=0, columnspan=2, padx=20, pady=(0,10), sticky="ew"); self.progressbar.set(0)
        self.stop_button = ctk.CTkButton(status_card, text="STOP CURRENT PROCESS", height=35, fg_color="#D32F2F", hover_color="#B71C1C", command=self.engine.stop_process)
        self.stop_button.grid(row=2, column=0, columnspan=2, padx=20, pady=(5, 15), sticky="ew")
        
        return frame

    def _create_config_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#2b2b2b")
        frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_frame, text="Settings & Parameters", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        self.save_config_button = ctk.CTkButton(header_frame, text="Save Configuration", command=self._save_gui_config)
        self.save_config_button.grid(row=0, column=1, sticky="e")
        
        tab_view = ctk.CTkTabview(frame, anchor="w", fg_color="#242424")
        tab_view.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        tab_view.add("Data Sources"); tab_view.add("Swing Rules"); tab_view.add("Momentum Rules"); tab_view.add("Export")
        self.cfg_vars = {} 
        self._populate_files_tab(tab_view.tab("Data Sources"))
        self._populate_rules_tab(tab_view.tab("Swing Rules"), "swing_rules")
        self._populate_rules_tab(tab_view.tab("Momentum Rules"), "momentum_rules")
        self._populate_export_tab(tab_view.tab("Export"))
        
        return frame
    
    def _create_logs_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#2b2b2b")
        frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Application Logs", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.log_textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), wrap="word", state="disabled", fg_color="#212121", border_width=1, border_color="gray25")
        self.log_textbox.grid(row=1, column=0, padx=20, pady=(0,20), sticky="nsew")
        self.log_textbox.tag_config('SUCCESS', foreground="#A3BE8C"); self.log_textbox.tag_config('ERROR', foreground="#BF616A"); self.log_textbox.tag_config('WARNING', foreground="#EBCB8B"); self.log_textbox.tag_config('INFO', foreground="#88C0D0"); self.log_textbox.tag_config('HEADER', foreground="#81A1C1")
        return frame

    # --- Configuration Tab Population ---
    def _populate_export_tab(self, tab):
        frame = ctk.CTkFrame(tab, fg_color="transparent"); frame.pack(fill="both", expand=True, padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Excel Format").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        excel_format_var = ctk.StringVar(value=self.config['export_settings'].get('excel_format', ''))
        self.cfg_vars["export_settings_excel_format"] = excel_format_var
        ctk.CTkOptionMenu(frame, variable=excel_format_var, values=["Single File with Multiple Sheets", "Individual File per Analysis"]).grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(frame, text="Export Folder").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        output_dir_var = ctk.StringVar(value=self.config['file_paths'].get('output_dir', ''))
        self.cfg_vars["file_paths_output_dir"] = output_dir_var
        entry = ctk.CTkEntry(frame, textvariable=output_dir_var); entry.grid(row=1, column=1, padx=(10,0), pady=10, sticky="ew")
        button = ctk.CTkButton(frame, text="Browse", width=80, command=lambda v=output_dir_var: v.set(filedialog.askdirectory(title="Select Export Folder") or v.get())); button.grid(row=1, column=2, padx=(5,10), pady=10)
        frame.grid_columnconfigure(2, weight=0)

    def _populate_files_tab(self, tab):
        url_frame = ctk.CTkFrame(tab, fg_color="transparent"); url_frame.pack(fill="both", expand=True, padx=5, pady=5)
        url_frame.grid_columnconfigure(1, weight=1)
        for i, (key, text) in enumerate([("nifty500_tickers_url", "Nifty 500 Tickers URL"), ("fno_tickers_url", "F&O Tickers URL")]):
            ctk.CTkLabel(url_frame, text=text).grid(row=i, column=0, padx=10, pady=10, sticky="w")
            var = ctk.StringVar(value=self.config['data_urls'].get(key, ''))
            self.cfg_vars[f"data_urls_{key}"] = var
            ctk.CTkEntry(url_frame, textvariable=var).grid(row=i, column=1, padx=10, pady=10, sticky="ew")
                
    def _populate_rules_tab(self, tab, rules_key):
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", label_text=f"{rules_key.replace('_', ' ').title()}"); scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        scroll_frame.grid_columnconfigure(1, weight=1)
        for i, (key, value) in enumerate(self.config.get(rules_key, {}).items()):
            var = ctk.StringVar(value=value); self.cfg_vars[f"{rules_key}_{key}"] = var
            label = ctk.CTkLabel(scroll_frame, text=key.replace('_', ' ').title()); label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(scroll_frame, textvariable=var); entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")

    # --- Config Saving & Loading ---
    def _save_gui_config(self):
        current_cfg = self._get_current_config()
        try:
            with open("source/config.json", "w") as f: json.dump(current_cfg, f, indent=4)
            self.engine.config = current_cfg; self.log("SUCCESS: Configuration saved.", "SUCCESS")
        except Exception as e: self.log(f"ERROR: Failed to save config: {e}", "ERROR")

    def _get_current_config(self):
        cfg = self.engine.config.copy()
        for key, var in self.data_fetch_vars.items(): cfg["data_settings"][key] = var.get()
        for key, var in self.cfg_vars.items():
            value = var.get()
            if isinstance(value, str):
                try: value = float(value) if "." in value else int(value)
                except ValueError: pass
            parts = key.split('_'); section = parts[0]; sub_section = "_".join(parts[1:])
            if section == "swing" and sub_section.startswith("rules"): cfg["swing_rules"]["_".join(parts[2:])] = value
            elif section == "momentum" and sub_section.startswith("rules"): cfg["momentum_rules"]["_".join(parts[2:])] = value
            elif section == "export" and sub_section.startswith("settings"): cfg["export_settings"]["_".join(parts[2:])] = value
            elif section == "file" and sub_section.startswith("paths"): cfg["file_paths"]["_".join(parts[2:])] = value
            elif section == "data" and sub_section.startswith("urls"): cfg["data_urls"]["_".join(parts[2:])] = value
        return cfg

    def update_progress(self, value, text):
        self.progressbar.set(value); self.status_label.configure(text=text)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.title("Signal Engine"); root.geometry("1280x720")
    engine = Engine(log_callback=print, progress_callback=lambda v,t: print(f"{v*100:.0f}%: {t}"))
    app = AppGUI(parent=root, engine=engine)
    app.pack(fill="both", expand=True)
    engine.log = app.log; engine.update_progress = app.update_progress
    root.mainloop()
