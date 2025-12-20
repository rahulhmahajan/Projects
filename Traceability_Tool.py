import os
import threading
import queue
import time
import json
import hashlib
import csv
from datetime import datetime
from difflib import get_close_matches
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

"""
Traceability_Tool_NoBackend.py

This variant removes the SQLite "backend" entirely and uses a local integrity
database (JSON) instead. The integrity DB is simply a JSON file containing
file metadata and SHA256 checksums. The app supports:

 1) Create Integrity DB (scan a folder and write integrity JSON).
 2) Create Config (.json) either from a folder or from the integrity DB.
 3) Perform traceability comparing the config against the integrity DB
    and produce a CSV report.

Long-running tasks run in background threads and log to the GUI.
"""

# --- Utilities --------------------------------------------------------------

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# --- Background worker and logging -----------------------------------------

class BGWorker:
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put("[{}] {}".format(timestamp, msg))

# --- Integrity DB creation (JSON) ------------------------------------------

def create_integrity_db_from_folder(integrity_json_path, folder_path, log_queue, on_complete=None):
    w = BGWorker(log_queue)
    def job():
        try:
            ensure_dir(os.path.dirname(integrity_json_path) or ".")
            w.log("Creating integrity DB at: {} from folder: {}".format(integrity_json_path, folder_path))
            entries = []
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    try:
                        fp = os.path.join(root, fn)
                        size = os.path.getsize(fp)
                        sha = sha256_of_file(fp)
                        mtime = os.path.getmtime(fp)
                        entry = {
                            "filename": fn,
                            "filepath": os.path.abspath(fp),
                            "size": size,
                            "mtime": datetime.fromtimestamp(mtime).isoformat(),
                            "sha256": sha
                        }
                        entries.append(entry)
                        w.log("Indexed: {}".format(fp))
                    except Exception as e:
                        w.log("Error indexing {}: {}".format(fp, e))
            with open(integrity_json_path, "w", encoding="utf-8") as f:
                json.dump({"files": entries}, f, indent=2)
            w.log("Integrity DB written: {} ({} entries)".format(integrity_json_path, len(entries)))
        except Exception as e:
            w.log("Fatal error: {}".format(e))
        finally:
            if on_complete:
                on_complete()
    threading.Thread(target=job, daemon=True).start()

# --- Config .json generation ------------------------------------------------

def create_config_from_folder(folder_path, output_json_path, log_queue, on_complete=None):
    w = BGWorker(log_queue)
    def job():
        try:
            w.log("Generating config.json from folder: {}".format(folder_path))
            entries = []
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    fp = os.path.join(root, fn)
                    size = os.path.getsize(fp)
                    mtime = os.path.getmtime(fp)
                    sha = sha256_of_file(fp)
                    entries.append({
                        "filename": fn,
                        "filepath": os.path.abspath(fp),
                        "size": size,
                        "mtime": datetime.fromtimestamp(mtime).isoformat(),
                        "sha256": sha
                    })
                    w.log("Found: {}".format(fn))
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump({"files": entries}, f, indent=2)
            w.log("Config written to: {} ({} entries)".format(output_json_path, len(entries)))
        except Exception as e:
            w.log("Error generating config: {}".format(e))
        finally:
            if on_complete:
                on_complete()
    threading.Thread(target=job, daemon=True).start()

def create_config_from_integrity(integrity_json_path, output_json_path, log_queue, on_complete=None):
    w = BGWorker(log_queue)
    def job():
        try:
            w.log("Generating config.json from integrity DB: {}".format(integrity_json_path))
            with open(integrity_json_path, "r", encoding="utf-8") as f:
                integrity = json.load(f)
            entries = []
            for it in integrity.get("files", []):
                entries.append({
                    "filename": it.get("filename"),
                    "filepath": it.get("filepath"),
                    "size": it.get("size"),
                    "sha256": it.get("sha256"),
                    "mtime": it.get("mtime")
                })
                w.log("Integrity entry: {}".format(it.get('filename')))
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump({"files": entries}, f, indent=2)
            w.log("Config written to: {} ({} entries)".format(output_json_path, len(entries)))
        except Exception as e:
            w.log("Error generating config from integrity DB: {}".format(e))
        finally:
            if on_complete:
                on_complete()
    threading.Thread(target=job, daemon=True).start()

# --- Traceability (simple matching) ----------------------------------------

def perform_traceability_integrity(integrity_json_path, config_json_path, report_csv_path, log_queue, on_complete=None):
    w = BGWorker(log_queue)
    def job():
        try:
            w.log("Starting traceability (integrity DB)...")
            with open(integrity_json_path, "r", encoding="utf-8") as f:
                integrity = json.load(f)
            db_rows = integrity.get("files", [])
            db_map = {r["filename"]: {"filepath": r["filepath"], "sha256": r.get("sha256")} for r in db_rows}
            with open(config_json_path, "r", encoding="utf-8") as f:
                conf = json.load(f)
            conf_files = conf.get("files", [])
            results = []
            db_filenames = list(db_map.keys())
            for item in conf_files:
                fn = item.get("filename")
                best = None
                score = 0.0
                if fn in db_map:
                    best = fn
                    score = 1.0
                    w.log("Exact match for {}".format(fn))
                else:
                    matches = get_close_matches(fn, db_filenames, n=1, cutoff=0.6)
                    if matches:
                        best = matches[0]
                        score = 0.75
                        w.log("Fuzzy match for {} -> {}".format(fn, best))
                results.append({
                    "config_filename": fn,
                    "config_filepath": item.get("filepath"),
                    "matched_db_filename": best,
                    "matched_db_filepath": db_map[best]["filepath"] if best else None,
                    "match_score": score,
                    "config_sha256": item.get("sha256"),
                    "db_sha256": db_map[best]["sha256"] if best else None
                })
            # Write CSV report
            with open(report_csv_path, "w", newline='', encoding="utf-8") as csvf:
                writer = csv.DictWriter(csvf, fieldnames=[
                    "config_filename", "config_filepath", "matched_db_filename",
                    "matched_db_filepath", "match_score", "config_sha256", "db_sha256"
                ])
                writer.writeheader()
                for r in results:
                    writer.writerow(r)
            w.log("Traceability finished. Report: {}".format(report_csv_path))
        except Exception as e:
            w.log("Error during traceability: {}".format(e))
        finally:
            if on_complete:
                on_complete()
    threading.Thread(target=job, daemon=True).start()

# --- GUI -------------------------------------------------------------------

class TraceabilityApp(tk.Tk):
    def __init__(self):
        super(TraceabilityApp, self).__init__()
        self.title("Traceability Tool (Integrity DB, no backend)")
        self.geometry("900x600")
        self.log_queue = queue.Queue()
        self.create_widgets()
        self.after(200, self.process_log_queue)

    def create_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab 1: Create Integrity DB
        tab_db = ttk.Frame(nb)
        nb.add(tab_db, text="1. Create Integrity DB")

        f1 = ttk.LabelFrame(tab_db, text="Integrity DB Target")
        f1.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(f1, text="Integrity JSON file:").pack(side=tk.LEFT, padx=4, pady=6)
        self.integrity_path_var = tk.StringVar(value=os.path.abspath("integrity_db.json"))
        ttk.Entry(f1, textvariable=self.integrity_path_var, width=60).pack(side=tk.LEFT, padx=4)
        ttk.Button(f1, text="Browse", command=self.browse_integrity_save).pack(side=tk.LEFT, padx=4)

        f3 = ttk.LabelFrame(tab_db, text="Scan Folder")
        f3.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(f3, text="Folder to scan:").pack(side=tk.LEFT, padx=4)
        self.import_folder_var = tk.StringVar()
        ttk.Entry(f3, textvariable=self.import_folder_var, width=60).pack(side=tk.LEFT, padx=4)
        ttk.Button(f3, text="Browse", command=self.browse_import_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(f3, text="Create Integrity DB from Folder", command=self.on_create_integrity_db_from_folder).pack(side=tk.LEFT, padx=8)

        # Tab 2: Create Config
        tab_cfg = ttk.Frame(nb)
        nb.add(tab_cfg, text="2. Create Config (.json)")

        cfg1 = ttk.LabelFrame(tab_cfg, text="Source")
        cfg1.pack(fill=tk.X, padx=8, pady=6)
        self.cfg_source_mode = tk.StringVar(value="folder")
        ttk.Radiobutton(cfg1, text="From Folder", variable=self.cfg_source_mode, value="folder").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(cfg1, text="From Integrity DB", variable=self.cfg_source_mode, value="integrity").pack(side=tk.LEFT, padx=4)

        cfg_folder_frame = ttk.Frame(cfg1)
        cfg_folder_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(cfg_folder_frame, text="Folder:").pack(side=tk.LEFT)
        self.cfg_folder_var = tk.StringVar()
        ttk.Entry(cfg_folder_frame, textvariable=self.cfg_folder_var, width=50).pack(side=tk.LEFT, padx=4)
        ttk.Button(cfg_folder_frame, text="Browse", command=self.browse_cfg_folder).pack(side=tk.LEFT, padx=4)

        cfg_db_frame = ttk.Frame(cfg1)
        cfg_db_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(cfg_db_frame, text="Integrity JSON:").pack(side=tk.LEFT)
        self.cfg_integrity_var = tk.StringVar()
        ttk.Entry(cfg_db_frame, textvariable=self.cfg_integrity_var, width=50).pack(side=tk.LEFT, padx=4)
        ttk.Button(cfg_db_frame, text="Browse", command=self.browse_cfg_integrity).pack(side=tk.LEFT, padx=4)

        cfg_out_frame = ttk.Frame(tab_cfg)
        cfg_out_frame.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(cfg_out_frame, text="Output JSON:").pack(side=tk.LEFT)
        self.cfg_out_var = tk.StringVar(value=os.path.abspath("config.json"))
        ttk.Entry(cfg_out_frame, textvariable=self.cfg_out_var, width=60).pack(side=tk.LEFT, padx=4)
        ttk.Button(cfg_out_frame, text="Browse", command=self.browse_cfg_out).pack(side=tk.LEFT, padx=4)
        ttk.Button(cfg_out_frame, text="Generate Config", command=self.on_generate_config).pack(side=tk.LEFT, padx=8)

        # Tab 3: Traceability
        tab_trace = ttk.Frame(nb)
        nb.add(tab_trace, text="3. Perform Traceability")

        tr_frame = ttk.LabelFrame(tab_trace, text="Inputs")
        tr_frame.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(tr_frame, text="Integrity JSON:").pack(side=tk.LEFT, padx=4)
        self.tr_integrity_var = tk.StringVar()
        ttk.Entry(tr_frame, textvariable=self.tr_integrity_var, width=50).pack(side=tk.LEFT, padx=4)
        ttk.Button(tr_frame, text="Browse", command=self.browse_tr_integrity).pack(side=tk.LEFT, padx=4)

        ttk.Label(tr_frame, text="Config JSON:").pack(side=tk.LEFT, padx=4)
        self.tr_cfg_var = tk.StringVar()
        ttk.Entry(tr_frame, textvariable=self.tr_cfg_var, width=50).pack(side=tk.LEFT, padx=4)
        ttk.Button(tr_frame, text="Browse", command=self.browse_tr_cfg).pack(side=tk.LEFT, padx=4)

        tr_out_frame = ttk.Frame(tab_trace)
        tr_out_frame.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(tr_out_frame, text="Report CSV:").pack(side=tk.LEFT)
        self.tr_report_var = tk.StringVar(value=os.path.abspath("trace_report.csv"))
        ttk.Entry(tr_out_frame, textvariable=self.tr_report_var, width=60).pack(side=tk.LEFT, padx=4)
        ttk.Button(tr_out_frame, text="Browse", command=self.browse_tr_report).pack(side=tk.LEFT, padx=4)
        ttk.Button(tr_out_frame, text="Run Traceability", command=self.on_run_traceability).pack(side=tk.LEFT, padx=8)

        # Log area
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.log_text.configure(state=tk.DISABLED)

    # --- Browse helpers -----------------------------------------------------
    def browse_integrity_save(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json"),("All","*.*")])
        if p:
            self.integrity_path_var.set(p)

    def browse_import_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.import_folder_var.set(p)

    def browse_cfg_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.cfg_folder_var.set(p)

    def browse_cfg_integrity(self):
        p = filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if p:
            self.cfg_integrity_var.set(p)

    def browse_cfg_out(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if p:
            self.cfg_out_var.set(p)

    def browse_tr_integrity(self):
        p = filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if p:
            self.tr_integrity_var.set(p)

    def browse_tr_cfg(self):
        p = filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if p:
            self.tr_cfg_var.set(p)

    def browse_tr_report(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if p:
            self.tr_report_var.set(p)

    # --- Actions ------------------------------------------------------------
    def on_create_integrity_db_from_folder(self):
        target = self.integrity_path_var.get().strip()
        folder = self.import_folder_var.get().strip()
        if not target or not folder:
            messagebox.showerror("Error", "Please set integrity JSON path and folder to scan.")
            return
        create_integrity_db_from_folder(target, folder, self.log_queue)

    def on_generate_config(self):
        out = self.cfg_out_var.get().strip()
        if not out:
            messagebox.showerror("Error", "Please choose output JSON path.")
            return
        mode = self.cfg_source_mode.get()
        if mode == "folder":
            folder = self.cfg_folder_var.get().strip()
            if not folder:
                messagebox.showerror("Error", "Please choose a folder to generate config from.")
                return
            create_config_from_folder(folder, out, self.log_queue)
        else:
            integrity = self.cfg_integrity_var.get().strip()
            if not integrity:
                messagebox.showerror("Error", "Please choose an integrity JSON file.")
                return
            create_config_from_integrity(integrity, out, self.log_queue)

    def on_run_traceability(self):
        integrity = self.tr_integrity_var.get().strip()
        cfg = self.tr_cfg_var.get().strip()
        report = self.tr_report_var.get().strip()
        if not integrity or not cfg or not report:
            messagebox.showerror("Error", "Please provide integrity JSON, config JSON, and report path.")
            return
        perform_traceability_integrity(integrity, cfg, report, self.log_queue)

    # --- Log handling -------------------------------------------------------
    def process_log_queue(self):
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        self.after(200, self.process_log_queue)

if __name__ == "__main__":
    app = TraceabilityApp()
    app.mainloop()
