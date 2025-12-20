import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import time
import os

#!/usr/bin/env python3
"""
Main_tool_GUI.PY

A compact, self-contained Tkinter GUI template updated to use multiple pages (tabs).
First page is "Main".
"""

APP_TITLE = "Main Tool GUI"
VERSION = "1.0"

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        self._current_file = None
        self._modified = False
        self._task_queue = queue.Queue()
        self._worker = None

        self._create_menu()
        self._create_toolbar()
        self._create_main_pages()   # now creates a Notebook with pages
        self._create_statusbar()
        self._bind_shortcuts()

        self.after(100, self._poll_queue)

    # --- UI creation ---------------------------------------------------
    def _create_menu(self):
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        filem.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        filem.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        filem.add_command(label="Save As...", command=self.save_as)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=filem)

        toolm = tk.Menu(menubar, tearoff=0)
        toolm.add_command(label="Run Task", command=self.run_task)
        toolm.add_command(label="Settings...", command=self.show_settings)
        menubar.add_cascade(label="Tools", menu=toolm)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpm)

        self.config(menu=menubar)

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, relief="raised")
        toolbar.pack(side="top", fill="x")

        b_new = ttk.Button(toolbar, text="New", command=self.new_file)
        b_open = ttk.Button(toolbar, text="Open", command=self.open_file)
        b_save = ttk.Button(toolbar, text="Save", command=self.save_file)
        b_run = ttk.Button(toolbar, text="Run", command=self.run_task)

        for b in (b_new, b_open, b_save, b_run):
            b.pack(side="left", padx=2, pady=2)

    def _create_main_pages(self):
        # Use a Notebook to create multiple pages/tabs. First tab is "Main".
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # --- Main page (first and default) ---
        main_page = ttk.Frame(notebook)
        notebook.add(main_page, text="Main")

        welcome = ttk.Label(main_page, text=f"Welcome to {APP_TITLE}", font=("TkDefaultFont", 14))
        welcome.pack(pady=20)

        desc = ttk.Label(main_page, text="Use the tabs to switch between pages. Editor and Tools are available.")
        desc.pack(pady=6)

        # Three prominent buttons on the Main page
        btn_frame = ttk.Frame(main_page)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="New File", command=self.new_file, width=18).pack(side="left", padx=8, pady=8)
        ttk.Button(btn_frame, text="Open File", command=self.open_file, width=18).pack(side="left", padx=8, pady=8)
        ttk.Button(btn_frame, text="Run Task", command=self.run_task, width=18).pack(side="left", padx=8, pady=8)

        # Recent files example area
        recent_label = ttk.Label(main_page, text="Recent files:")
        recent_label.pack(anchor="w", padx=10, pady=(10,0))
        self.recent_list = tk.Listbox(main_page, height=4)
        self.recent_list.pack(fill="x", padx=10, pady=5)

        # --- Editor page ---
        editor_page = ttk.Frame(notebook)
        notebook.add(editor_page, text="Editor")

        # editor: text widget and progress bar
        self.text = tk.Text(editor_page, wrap="none", undo=True)
        self.text.pack(fill="both", expand=True, padx=5, pady=5)
        self.text.bind("<<Modified>>", self._on_text_modified)

        progress_frame = ttk.Frame(editor_page)
        progress_frame.pack(fill="x", padx=5, pady=(0,5))
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill="x", expand=True)

        # --- Tools page ---
        tools_page = ttk.Frame(notebook)
        notebook.add(tools_page, text="Tools")

        self.tool_list = tk.Listbox(tools_page, exportselection=False)
        for item in ("Tool A", "Tool B", "Tool C", "Tool D"):
            self.tool_list.insert("end", item)
        self.tool_list.bind("<<ListboxSelect>>", self.on_tool_select)
        self.tool_list.pack(fill="both", expand=True, padx=5, pady=5)

        # expose notebook in case user wants to switch programmatically
        self.notebook = notebook

    def _create_statusbar(self):
        status = ttk.Frame(self, relief="sunken")
        status.pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side="left", padx=5)
        self.pos_label = ttk.Label(status, text="Ln 1, Col 1", anchor="e")
        self.pos_label.pack(side="right", padx=5)
        # bind cursor updates only if text exists
        if hasattr(self, "text"):
            self.text.bind("<KeyRelease>", self._update_cursor_pos)
            self.text.bind("<ButtonRelease>", self._update_cursor_pos)

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-s>", lambda e: self.save_file())

    # --- File operations -----------------------------------------------
    def new_file(self):
        if not self._confirm_discard_changes():
            return
        self.text.delete("1.0", "end")
        self._current_file = None
        self._modified = False
        self._update_title()
        self.status_var.set("New file")

    def open_file(self):
        if not self._confirm_discard_changes():
            return
        path = filedialog.askopenfilename(title="Open file", filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self._current_file = path
            self._modified = False
            self._update_title()
            self.status_var.set(f"Opened {os.path.basename(path)}")
            # add to recent list
            self._add_recent(path)
            # switch to editor tab
            try:
                idx = self.notebook.tabs().index(self.notebook.select())
            except Exception:
                pass
            self.notebook.select(1)  # Editor tab index
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def save_file(self):
        if self._current_file:
            return self._save_to(self._current_file)
        return self.save_as()

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return False
        res = self._save_to(path)
        if res:
            self._add_recent(path)
        return res

    def _save_to(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            self._current_file = path
            self._modified = False
            self._update_title()
            self.status_var.set(f"Saved {os.path.basename(path)}")
            return True
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return False

    def _add_recent(self, path):
        # simple recent list; avoid duplicates
        base = os.path.basename(path)
        entries = list(self.recent_list.get(0, "end"))
        if base in entries:
            return
        self.recent_list.insert(0, base)
        # keep max 10
        if self.recent_list.size() > 10:
            self.recent_list.delete(10, "end")

    def _confirm_discard_changes(self):
        if self._modified:
            res = messagebox.askyesnocancel("Unsaved changes", "You have unsaved changes. Save before continuing?")
            if res is None:
                return False
            if res:
                return self.save_file()
        return True

    def _update_title(self):
        name = os.path.basename(self._current_file) if self._current_file else "Untitled"
        mod = "*" if self._modified else ""
        self.title(f"{name}{mod} - {APP_TITLE}")

    def _on_text_modified(self, event=None):
        if self.text.edit_modified():
            self._modified = True
            self._update_title()
            self.text.edit_modified(False)

    def _update_cursor_pos(self, event=None):
        try:
            idx = self.text.index("insert")
            line, col = idx.split(".")
            self.pos_label.config(text=f"Ln {line}, Col {int(col)+1}")
        except Exception:
            pass

    # --- Tool interactions ---------------------------------------------
    def on_tool_select(self, event=None):
        sel = self.tool_list.curselection()
        if not sel:
            return
        tool = self.tool_list.get(sel[0])
        self.status_var.set(f"Selected: {tool}")
        # Example: insert tool name to editor (ensure editor exists)
        if hasattr(self, "text"):
            self.text.insert("insert", f"[{tool}] ")

    # --- Background task runner ---------------------------------------
    def run_task(self):
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("Task running", "A task is already running.")
            return
        # ensure progress exists (created with editor)
        if not hasattr(self, "progress"):
            messagebox.showinfo("No progress", "No progress bar available.")
            return
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.status_var.set("Task started")
        # Start worker thread
        self._worker = threading.Thread(target=self._background_task, daemon=True)
        self._worker.start()

    def _background_task(self):
        try:
            for i in range(101):
                time.sleep(0.03)  # simulate work
                self._task_queue.put(("progress", i))
            self._task_queue.put(("done", "Task completed"))
        except Exception as e:
            self._task_queue.put(("error", str(e)))

    def _poll_queue(self):
        try:
            while True:
                msg = self._task_queue.get_nowait()
                typ = msg[0]
                if typ == "progress":
                    val = msg[1]
                    if hasattr(self, "progress"):
                        self.progress["value"] = val
                    self.status_var.set(f"Progress: {val}%")
                elif typ == "done":
                    self.status_var.set(msg[1])
                    if hasattr(self, "progress"):
                        self.progress["value"] = 0
                elif typ == "error":
                    messagebox.showerror("Task error", msg[1])
                    self.status_var.set("Error during task")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # --- Settings & About ---------------------------------------------
    def show_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Settings")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        ttk.Label(dlg, text="Font size:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        font_size = tk.IntVar(value=12)
        spin = ttk.Spinbox(dlg, from_=8, to=36, textvariable=font_size, width=5)
        spin.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(dlg, text="Auto-save (sec):").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        autosave = tk.IntVar(value=0)
        ttk.Entry(dlg, textvariable=autosave, width=8).grid(row=1, column=1, padx=8, pady=4)

        def apply_and_close():
            try:
                size = int(font_size.get())
                if hasattr(self, "text"):
                    self.text.config(font=("TkDefaultFont", size))
            except Exception:
                pass
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=apply_and_close).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side="left", padx=5)

    def show_about(self):
        messagebox.showinfo("About", f"{APP_TITLE}\nVersion {VERSION}")

    # --- Exit ---------------------------------------------------------
    def on_exit(self):
        if not self._confirm_discard_changes():
            return
        self.destroy()

def main():
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()