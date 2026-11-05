import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

GR5_DRIVE = "Y:"
GR6_DRIVE = "Z:"


class GR5vsGR6App:
    def __init__(self, root):
        self.root = root
        self.root.title("GR5 Vs GR6")
        self.root.geometry("600x400")

        self.build_root = None          # e.g. D:\Builds
        self.mapped_drives = []         # drives created by this app

        self._build_menu()

        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_gradient())

        self._build_panel()
        self.draw_gradient()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
        path = filedialog.askdirectory(title="Select Build Area", mustexist=True)
        if not path:
            return
        path = os.path.normpath(path)

        types = self._subdirs(path)
        if not types:
            messagebox.showwarning("No builds", f"No sub-folders found in:\n{path}")
            return

        self.reset()
        self.build_root = path
        self.area_label.config(text=path)
        self.type_cb.config(values=types, state="readonly")

    def on_type_selected(self, _event=None):
        type_path = os.path.join(self.build_root, self.type_var.get())
        builds = self._subdirs(type_path)

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

        # Release any drives this app mapped earlier, then map fresh ones.
        self.unmap_drives()
        try:
            self.map_drive(GR5_DRIVE, gr5_path)
            self.map_drive(GR6_DRIVE, gr6_path)
        except RuntimeError as exc:
            self.unmap_drives()
            messagebox.showerror("Drive mapping failed", str(exc))
            return

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
        result = subprocess.run(
            ["subst", drive, path],
            capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"subst {drive} failed")
        self.mapped_drives.append(drive)

    def unmap_drives(self):
        for drive in self.mapped_drives:
            subprocess.run(
                ["subst", drive, "/d"], capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        self.mapped_drives.clear()

    def on_close(self):
        self.unmap_drives()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    GR5vsGR6App(root)
    root.mainloop()