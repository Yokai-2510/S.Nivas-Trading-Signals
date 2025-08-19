# --- app.py (Corrected) ---
import customtkinter as ctk
from tkinter import filedialog
import json
import os
from main import Engine

class AppGUI(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.engine = engine; self.config = engine.config
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)

        # Create all frames
        self.nav_frame = self._create_nav_frame()
        self.dashboard_frame = self._create_dashboard_frame()
        self.config_frame = self._create_config_frame()
        self.logs_frame = self._create_logs_frame()
        
        # Place frames
        self.nav_frame.grid(row=0, column=0, sticky="nsw", padx=10, pady=10)
        self.dashboard_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        self.update_ui_state("IDLE") # Set initial button states

    def update_ui_state(self, state):
        if state == "IDLE":
            self.fetch_button.configure(state="normal"); self.run_button.configure(state="disabled"); self.export_button.configure(state="disabled")
            self.save_config_button.configure(state="normal"); self.stop_button.configure(state="disabled")
        elif state == "BUSY":
            self.fetch_button.configure(state="disabled"); self.run_button.configure(state="disabled"); self.export_button.configure(state="disabled")
            self.save_config_button.configure(state="disabled"); self.stop_button.configure(state="normal")
        elif state == "ANALYSIS_READY":
            self.fetch_button.configure(state="normal"); self.run_button.configure(state="normal"); self.export_button.configure(state="disabled")
            self.save_config_button.configure(state="normal"); self.stop_button.configure(state="disabled")
        elif state == "EXPORT_READY":
            self.fetch_button.configure(state="normal"); self.run_button.configure(state="normal"); self.export_button.configure(state="normal")
            self.save_config_button.configure(state="normal"); self.stop_button.configure(state="disabled")

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

    # --- UI Creation methods ---

    def _select_frame_by_name(self, name):
        self.dashboard_frame.grid_forget(); self.config_frame.grid_forget(); self.logs_frame.grid_forget()
        if name == "dashboard": self.dashboard_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        elif name == "config": self.config_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        elif name == "logs": self.logs_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)

    def _create_nav_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.grid_rowconfigure(4, weight=1)
        ctk.CTkLabel(frame, text="Signal Engine", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkButton(frame, text="Dashboard", command=lambda: self._select_frame_by_name("dashboard")).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(frame, text="Configuration", command=lambda: self._select_frame_by_name("config")).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(frame, text="Logs", command=lambda: self._select_frame_by_name("logs")).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        return frame

    def _create_dashboard_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure((0, 1, 2), weight=1); frame.grid_rowconfigure(3, weight=3)
        data_frame = ctk.CTkFrame(frame, corner_radius=10); data_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(data_frame, text="Step 1: Data Preparation", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        self.fetch_button = ctk.CTkButton(data_frame, text="FETCH LATEST DATA", height=35, font=ctk.CTkFont(size=14, weight="bold"), command=self.fetch_data_button_pressed)
        self.fetch_button.pack(fill="x", padx=20, pady=10)
        analysis_frame = ctk.CTkFrame(frame, corner_radius=10); analysis_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        analysis_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(analysis_frame, text="Step 2: Analysis on Local Data", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10,5))
        self.analysis_vars = {'N500_SWING': ctk.BooleanVar(value=True), 'N500_MOMENTUM': ctk.BooleanVar(value=True), 'FNO_SWING': ctk.BooleanVar(value=True), 'FNO_MOMENTUM': ctk.BooleanVar(value=True)}
        checkbox_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent"); checkbox_frame.grid(row=1, column=0, sticky="w", padx=15)
        for i, (key, var) in enumerate(self.analysis_vars.items()): ctk.CTkCheckBox(checkbox_frame, text=key.replace('_', ' - '), variable=var).grid(row=i//2, column=i%2, padx=5, pady=5, sticky="w")
        self.run_button = ctk.CTkButton(analysis_frame, text="RUN ANALYSIS", height=35, font=ctk.CTkFont(size=14, weight="bold"), command=self.run_analysis_button_pressed)
        self.run_button.grid(row=1, column=1, sticky="ew", padx=20, pady=10)
        export_frame = ctk.CTkFrame(frame, corner_radius=10); export_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(export_frame, text="Step 3: Export Results", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        self.export_button = ctk.CTkButton(export_frame, text="EXPORT RESULTS", height=35, font=ctk.CTkFont(size=14, weight="bold"), command=self.export_button_pressed)
        self.export_button.pack(fill="x", padx=20, pady=10)
        progress_frame = ctk.CTkFrame(frame); progress_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(10,10))
        progress_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(progress_frame, text="Status", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,0))
        self.status_label = ctk.CTkLabel(progress_frame, text="Idle", font=ctk.CTkFont(size=14)); self.status_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.progressbar = ctk.CTkProgressBar(progress_frame, progress_color="#4CAF50"); self.progressbar.grid(row=1, column=1, padx=10, pady=5, sticky="ew"); self.progressbar.set(0)
        self.stop_button = ctk.CTkButton(progress_frame, text="STOP CURRENT PROCESS", fg_color="#D32F2F", hover_color="#B71C1C", state="disabled", command=self.engine.stop_process)
        self.stop_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        return frame

    def _create_config_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10); frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Settings & Parameters", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        tab_view = ctk.CTkTabview(frame, anchor="w"); tab_view.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        tab_view.add("File & Data"); tab_view.add("Swing Rules"); tab_view.add("Momentum Rules"); tab_view.add("Export Settings")
        self.cfg_vars = {} 
        self._populate_files_tab(tab_view.tab("File & Data")); self._populate_rules_tab(tab_view.tab("Swing Rules"), "swing_rules")
        self._populate_rules_tab(tab_view.tab("Momentum Rules"), "momentum_rules"); self._populate_export_tab(tab_view.tab("Export Settings"))
        self.save_config_button = ctk.CTkButton(frame, text="Save Configuration", command=self._save_gui_config); self.save_config_button.grid(row=2, column=0, padx=20, pady=20, sticky="e")
        return frame
    
    def _create_logs_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=10); frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Application Logs", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.log_textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), wrap="word", state="disabled"); self.log_textbox.grid(row=1, column=0, padx=20, pady=(0,20), sticky="nsew")
        self.log_textbox.tag_config('SUCCESS', foreground="#A3BE8C"); self.log_textbox.tag_config('ERROR', foreground="#BF616A"); self.log_textbox.tag_config('WARNING', foreground="#EBCB8B"); self.log_textbox.tag_config('INFO', foreground="#88C0D0"); self.log_textbox.tag_config('HEADER', foreground="#81A1C1")
        return frame

    def _populate_export_tab(self, tab):
        frame = ctk.CTkFrame(tab); frame.pack(fill="both", expand=True, padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)
        
        # --- Row 0: Excel Format ---
        ctk.CTkLabel(frame, text="Excel Format").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        excel_format_var = ctk.StringVar(value=self.config['export_settings'].get('excel_format', ''))
        self.cfg_vars["export_settings_excel_format"] = excel_format_var
        ctk.CTkOptionMenu(frame, variable=excel_format_var, values=["Single File with Multiple Sheets", "Individual File per Analysis"]).grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Row 1: Output Directory ---
        ctk.CTkLabel(frame, text="Export Folder").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        output_dir_var = ctk.StringVar(value=self.config['file_paths'].get('output_dir', ''))
        self.cfg_vars["file_paths_output_dir"] = output_dir_var
        entry = ctk.CTkEntry(frame, textvariable=output_dir_var)
        entry.grid(row=1, column=1, padx=(10,0), pady=10, sticky="ew")
        button = ctk.CTkButton(frame, text="Browse", width=80, command=lambda v=output_dir_var: v.set(filedialog.askdirectory(title="Select Export Folder") or v.get()))
        button.grid(row=1, column=2, padx=(5,10), pady=10)
        frame.grid_columnconfigure(2, weight=0)

    def _populate_files_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)
        
        # --- Data Fetch Options Frame ---
        fetch_frame = ctk.CTkFrame(tab); fetch_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        fetch_frame.grid_columnconfigure((0,1), weight=1)
        for i, (key, label) in enumerate([("n500", "Nifty 500 Data"), ("fno", "F&O Data")]):
            frame = ctk.CTkFrame(fetch_frame); frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            for sub_key, text in [("fetch_tickers", "Download fresh Ticker list"), ("fetch_ohlcv", "Download fresh OHLCV data")]:
                var_key = f"{key}_{sub_key}"; var = ctk.BooleanVar(value=self.config["data_settings"].get(var_key, False))
                self.cfg_vars[var_key] = var
                ctk.CTkCheckBox(frame, text=text, variable=var).pack(anchor="w", padx=10, pady=5)
        
        # --- Data URLs Frame ---
        url_frame = ctk.CTkFrame(tab); url_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        url_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(url_frame, text="Data Source URLs", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        for i, (key, text) in enumerate([("nifty500_tickers_url", "Nifty 500 Tickers URL"), ("fno_tickers_url", "F&O Tickers URL")]):
            ctk.CTkLabel(url_frame, text=text).grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            var = ctk.StringVar(value=self.config['data_urls'].get(key, ''))
            self.cfg_vars[f"data_urls_{key}"] = var
            ctk.CTkEntry(url_frame, textvariable=var).grid(row=i+1, column=1, padx=10, pady=5, sticky="ew")

    def _populate_rules_tab(self, tab, rules_key):
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text=f"{rules_key.replace('_', ' ').title()}"); scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_frame.grid_columnconfigure(1, weight=1)
        for i, (key, value) in enumerate(self.config.get(rules_key, {}).items()):
            var = ctk.StringVar(value=value)
            self.cfg_vars[f"{rules_key}_{key}"] = var
            label = ctk.CTkLabel(scroll_frame, text=key.replace('_', ' ').title()); label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(scroll_frame, textvariable=var); entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")

    def _save_gui_config(self):
        current_cfg = self._get_current_config()
        try:
            with open("source/config.json", "w") as f: json.dump(current_cfg, f, indent=4)
            self.engine.config = current_cfg
            self.log("SUCCESS: Configuration saved.", "SUCCESS")
        except Exception as e: self.log(f"ERROR: Failed to save config: {e}", "ERROR")

    def _get_current_config(self):
        cfg = self.engine.config.copy()
        for key, var in self.cfg_vars.items():
            value = var.get()
            if isinstance(value, str):
                try: value = float(value) if "." in value else int(value)
                except ValueError: pass
            
            # Split the key to find the correct dictionary path
            parts = key.split('_')
            section = parts[0]
            sub_section = "_".join(parts[1:])
            
            if section == "swing" and sub_section.startswith("rules"):
                cfg["swing_rules"]["_".join(parts[2:])] = value
            elif section == "momentum" and sub_section.startswith("rules"):
                cfg["momentum_rules"]["_".join(parts[2:])] = value
            elif section == "export" and sub_section.startswith("settings"):
                cfg["export_settings"]["_".join(parts[2:])] = value
            elif section == "file" and sub_section.startswith("paths"):
                 cfg["file_paths"]["_".join(parts[2:])] = value
            elif section == "data" and sub_section.startswith("urls"):
                 cfg["data_urls"]["_".join(parts[2:])] = value
            else:
                cfg["data_settings"][key] = value
        return cfg

    def update_progress(self, value, text):
        self.progressbar.set(value); self.status_label.configure(text=text)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.title("Signal Engine"); root.geometry("1200x850")
    engine = Engine(log_callback=print, progress_callback=lambda v,t: print(f"{v*100:.0f}%: {t}"))
    app = AppGUI(parent=root, engine=engine)
    app.pack(fill="both", expand=True)
    engine.log = app.log; engine.update_progress = app.update_progress
    root.mainloop()