import os
import sys
import queue
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

GR5_DRIVE = "Y:"
GR6_DRIVE = "Z:"
LOG_LINES = 20  # visible lines in the log box (minimum)


class TextRedirector:
    """File-like object: copies everything written to the real console
    (so the CMD prompt still shows it) and queues it for the GUI log box."""

    def __init__(self, original, log_queue):
        self.original = original
        self.log_queue = log_queue

    def write(self, text):
        if self.original is not None:
            try:
                self.original.write(text)
                self.original.flush()
            except Exception:
                pass
        if text:
            self.log_queue.put(text)

    def flush(self):
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass


class GR5vsGR6App:
    def __init__(self, root):
        self.root = root
        self.root.title("GR5 Vs GR6")
        self.root.geometry("600x740")

        self.build_root = None          # e.g. D:\Builds
        self.mapped_drives = []         # drives created by this app

        self._build_menu()

        # Log box is packed first (bottom) so the gradient canvas gets the rest.
        self._build_log_box()

        self.canvas = tk.Canvas(root, height=400, highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_gradient())

        self._build_panel()
        self.draw_gradient()

        # Mirror console output (stdout + stderr) into the log box.
        self.log_queue = queue.Queue()
        self._orig_stdout, self._orig_stderr = sys.stdout, sys.stderr
        sys.stdout = TextRedirector(self._orig_stdout, self.log_queue)
        sys.stderr = TextRedirector(self._orig_stderr, self.log_queue)
        self.root.after(100, self._poll_log_queue)

        self.log("Application started.")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------- log box
    def _build_log_box(self):
        frame = tk.Frame(self.root)
        frame.pack(side="bottom", fill="x")

        tk.Label(frame, text="Log", anchor="w", font=("Georgia", 9, "bold")).pack(fill="x")

        inner = tk.Frame(frame)
        inner.pack(fill="x")

        self.log_text = tk.Text(
            inner, height=LOG_LINES, wrap="word", state="disabled",
            bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9),
        )
        scroll = ttk.Scrollbar(inner, orient="vertical", command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")

    def _poll_log_queue(self):
        chunks = []
        try:
            while True:
                chunks.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        if chunks:
            self.log_text.config(state="normal")
            self.log_text.insert("end", "".join(chunks))
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(100, self._poll_log_queue)

    def log(self, message):
        """Print a timestamped line (goes to CMD and the log box)."""
        print(f"[{datetime.now():%H:%M:%S}] {message}")

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        action = tk.Menu(menubar, tearoff=0)
        action.add_command(label="Select Build Area", command=self.select_build_area)
        action.add_command(label="Remove Temp Drives", command=self.unmap_drives)
        action.add_separator()
        action.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="Action", menu=action)

        edit = tk.Menu(menubar, tearoff=0)
        edit.add_command(label="Reset", command=self.reset)
        menubar.add_cascade(label="Edit", menu=edit)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About", "GR5 Vs GR6\nMaps two builds to temp drives (Y: and Z:)."
            ),
        )
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_panel(self):
        self.panel = tk.Frame(self.canvas, bg="white", padx=6, pady=10)
        self.canvas_window = self.canvas.create_window(
            300, 200, window=self.panel, anchor="center"
        )

        label_font = ("Georgia", 10, "bold")

        self.btn_area = tk.Button(
            self.panel, text="Select Build Area", font=label_font,
            bg="#fffacd", relief="solid", bd=2, command=self.select_build_area,
        )
        self.btn_area.pack(pady=(0, 8))

        self.area_label = tk.Label(self.panel, text="(none selected)",
                                   bg="white", fg="#555", font=("Georgia", 8))
        self.area_label.pack()

        # Build Type
        self._label("Build Type", label_font)
        self.type_var = tk.StringVar()
        self.type_cb = ttk.Combobox(self.panel, textvariable=self.type_var,
                                    state="disabled", width=28)
        self.type_cb.pack()
        self.type_cb.bind("<<ComboboxSelected>>", self.on_type_selected)

        # GR5
        self._label("GR5 Build", label_font)
        self.gr5_var = tk.StringVar()
        self.gr5_cb = ttk.Combobox(self.panel, textvariable=self.gr5_var,
                                   state="disabled", width=28)
        self.gr5_cb.pack()

        # GR6
        self._label("GR6 Build", label_font)
        self.gr6_var = tk.StringVar()
        self.gr6_cb = ttk.Combobox(self.panel, textvariable=self.gr6_var,
                                   state="disabled", width=28)
        self.gr6_cb.pack()

        self.btn_run = tk.Button(
            self.panel, text="RUN", font=label_font, bg="#ccff66",
            relief="solid", bd=2, width=6, command=self.run,
        )
        self.btn_run.pack(pady=(14, 0))

    def _label(self, text, font):
        tk.Label(self.panel, text=text, font=font, bg="white").pack(pady=(8, 2))

    def draw_gradient(self):
        """Draw a vertical gradient on the canvas."""
        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 400)
        color1 = "#eeaabf"  # light pink
        color2 = "#948be8"  # light purple

        self.canvas.delete("gradient")
        steps = height
        r1, g1, b1 = self.root.winfo_rgb(color1)
        r2, g2, b2 = self.root.winfo_rgb(color2)
        for i in range(steps):
            # winfo_rgb returns 16-bit values so we convert them to 8-bit.
            r = int(r1 + (r2 - r1) * i / steps) >> 8
            g = int(g1 + (g2 - g1) * i / steps) >> 8
            b = int(b1 + (b2 - b1) * i / steps) >> 8
            hex_color = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)
            self.canvas.create_line(0, i, width, i, fill=hex_color, tags="gradient")

        self.canvas.tag_lower("gradient")
        self.canvas.coords(self.canvas_window, width // 2, height // 2)

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _subdirs(path):
        try:
            return sorted(
                d for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))
            )
        except OSError:
            return []

    def reset(self):
        for var in (self.type_var, self.gr5_var, self.gr6_var):
            var.set("")
        for cb in (self.type_cb, self.gr5_cb, self.gr6_cb):
            cb.config(values=[], state="disabled")
        self.build_root = None
        self.area_label.config(text="(none selected)")

    # ------------------------------------------------------------ actions
    def select_build_area(self):
        self.log("Select Build Area clicked.")
        path = filedialog.askdirectory(title="Select Build Area", mustexist=True)
        if not path:
            self.log("No folder selected.")
            return
        path = os.path.normpath(path)

        types = self._subdirs(path)
        if not types:
            self.log(f"WARNING: no sub-folders found in {path}")
            messagebox.showwarning("No builds", f"No sub-folders found in:\n{path}")
            return

        self.reset()
        self.build_root = path
        self.area_label.config(text=path)
        self.type_cb.config(values=types, state="readonly")
        self.log(f"Build area: {path}")
        self.log(f"Build types found: {', '.join(types)}")

    def on_type_selected(self, _event=None):
        type_path = os.path.join(self.build_root, self.type_var.get())
        builds = self._subdirs(type_path)
        self.log(f"Build type '{self.type_var.get()}' selected: {len(builds)} build(s) found.")
        self.log(f"Builds: {', '.join(builds) if builds else '(none)'}")

        self.gr5_var.set("")
        self.gr6_var.set("")
        self.gr5_cb.config(values=builds, state="readonly")
        self.gr6_cb.config(values=builds, state="readonly")

    def run(self):
        if not self.build_root:
            messagebox.showwarning("Missing", "Select a build area first.")
            return

        build_type = self.type_var.get()
        gr5 = self.gr5_var.get()
        gr6 = self.gr6_var.get()
        if not (build_type and gr5 and gr6):
            messagebox.showwarning("Missing", "Select build type, GR5 build and GR6 build.")
            return
        if gr5 == gr6:
            if not messagebox.askyesno(
                "Same build", "GR5 and GR6 are the same build. Continue anyway?"
            ):
                return

        gr5_path = os.path.join(self.build_root, build_type, gr5)
        gr6_path = os.path.join(self.build_root, build_type, gr6)

        self.log("RUN clicked.")
        self.log(f"gr5_path = {gr5_path}")
        self.log(f"gr6_path = {gr6_path}")

        # Release any drives this app mapped earlier, then map fresh ones.
        self.unmap_drives()
        try:
            self.map_drive(GR5_DRIVE, gr5_path)
            self.map_drive(GR6_DRIVE, gr6_path)
        except RuntimeError as exc:
            self.log(f"ERROR: {exc}")
            self.unmap_drives()
            messagebox.showerror("Drive mapping failed", str(exc))
            return

        self.log("Temp drives ready.")
        messagebox.showinfo(
            "Ready",
            f"{GR5_DRIVE} -> {gr5_path}\n{GR6_DRIVE} -> {gr6_path}",
        )
        # TODO: launch the GR5 vs GR6 comparison here, using
        # GR5_DRIVE + "\\" and GR6_DRIVE + "\\" as the roots.

    # --------------------------------------------------------- temp drives
    def map_drive(self, drive, path):
        if os.path.exists(drive + "\\"):
            raise RuntimeError(f"Drive {drive} is already in use. Free it and try again.")
        cmd = ["subst", drive, path]
        self.log(f"> {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"subst {drive} failed")
        self.mapped_drives.append(drive)
        self.log(f"{drive} -> {path} (OK)")

    def unmap_drives(self):
        for drive in self.mapped_drives:
            cmd = ["subst", drive, "/d"]
            self.log(f"> {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.stdout.strip():
                print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip())
        if self.mapped_drives:
            self.log("Temp drives removed.")
        self.mapped_drives.clear()

    def on_close(self):
        self.log("Closing application.")
        self.unmap_drives()
        sys.stdout, sys.stderr = self._orig_stdout, self._orig_stderr
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    GR5vsGR6App(root)
    root.mainloop()