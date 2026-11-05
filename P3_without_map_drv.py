"""
GR5 Vs GR6 - build selector GUI
================================
Flow:
    1. "Select Build Area"  -> pick a root folder, e.g. D:\\Builds
    2. Build Type dropdown  -> sub-folders of the root      (Release / Debug)
    3. GR5 / GR6 dropdowns  -> sub-folders of the build type (Build_100, ...)
    4. RUN                  -> builds gr5_path / gr6_path and verifies them

Expected folder layout:
    D:\\Builds
    ├── Release
    │   ├── Build_100
    │   └── Build_101
    └── Debug
        ├── Build_100
        └── Build_101

Everything printed to the CMD prompt is also shown in the log box.
Look for the "# >>> MODIFY" markers for the places you are most likely to edit.
"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import os                                   # path handling / folder listing
import sys                                  # used to redirect stdout / stderr
import queue                                # thread-safe buffer for log text
import tkinter as tk                        # GUI toolkit
from datetime import datetime               # timestamps in the log
from tkinter import ttk, filedialog, messagebox

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
# >>> MODIFY: number of lines visible in the log box (keep at 20 or more)
LOG_LINES = 20


# ============================================================================
# Console -> log box redirection
# ============================================================================
class TextRedirector:
    """File-like object that replaces sys.stdout / sys.stderr.

    Whatever is printed is:
      * passed on to the real console (so the CMD prompt still shows it), and
      * put in a queue that the GUI reads to fill the log box.
    A queue is used (instead of writing to the Text widget directly) so that
    printing from any thread is safe.
    """

    def __init__(self, original, log_queue):
        self.original = original            # the real stdout / stderr
        self.log_queue = log_queue          # shared with the GUI

    def write(self, text):
        # 1) echo to the real console (may be None when run without a console)
        if self.original is not None:
            try:
                self.original.write(text)
                self.original.flush()
            except Exception:
                pass
        # 2) hand the text to the GUI
        if text:
            self.log_queue.put(text)

    def flush(self):
        # Required by the file-like interface.
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass


# ============================================================================
# Main application window
# ============================================================================
class GR5vsGR6App:
    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, root):
        self.root = root
        self.root.title("GR5 Vs GR6")
        # >>> MODIFY: window size (width x height). Make it taller if you
        #     increase LOG_LINES.
        self.root.geometry("600x740")

        # Root folder chosen with "Select Build Area" (e.g. D:\Builds).
        self.build_root = None

        self._build_menu()

        # The log box is packed FIRST (at the bottom) so the gradient canvas
        # takes whatever space is left above it.
        self._build_log_box()

        # Canvas that holds the gradient background and the white panel.
        self.canvas = tk.Canvas(root, height=400, highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)
        # Redraw the gradient whenever the window is resized.
        self.canvas.bind("<Configure>", lambda e: self.draw_gradient())

        self._build_panel()
        self.draw_gradient()

        # Mirror console output (stdout + stderr) into the log box.
        self.log_queue = queue.Queue()
        self._orig_stdout, self._orig_stderr = sys.stdout, sys.stderr
        sys.stdout = TextRedirector(self._orig_stdout, self.log_queue)
        sys.stderr = TextRedirector(self._orig_stderr, self.log_queue)
        # Start the timer that moves queued text into the log box.
        self.root.after(100, self._poll_log_queue)

        self.log("Application started.")
        # Make sure the console is restored when the window is closed.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------
    # Log box
    # ------------------------------------------------------------------
    def _build_log_box(self):
        """Create the read-only, scrollable log box at the bottom."""
        frame = tk.Frame(self.root)
        frame.pack(side="bottom", fill="x")

        tk.Label(frame, text="Log", anchor="w",
                 font=("Georgia", 9, "bold")).pack(fill="x")

        inner = tk.Frame(frame)
        inner.pack(fill="x")

        # >>> MODIFY: colours / font of the log box
        self.log_text = tk.Text(
            inner, height=LOG_LINES, wrap="word", state="disabled",
            bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9),
        )
        scroll = ttk.Scrollbar(inner, orient="vertical",
                               command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")

    def _poll_log_queue(self):
        """Runs every 100 ms: move queued console text into the log box."""
        chunks = []
        try:
            while True:
                chunks.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass

        if chunks:
            # The box is read-only, so unlock it just while inserting.
            self.log_text.config(state="normal")
            self.log_text.insert("end", "".join(chunks))
            self.log_text.see("end")            # auto-scroll to newest line
            self.log_text.config(state="disabled")

        self.root.after(100, self._poll_log_queue)

    def log(self, message):
        """Print a timestamped line (shows in CMD and in the log box).

        Use self.log("...") anywhere you want to add your own log messages.
        A plain print("...") works too.
        """
        print(f"[{datetime.now():%H:%M:%S}] {message}")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_menu(self):
        """Create the Action / Edit / Help menu bar."""
        menubar = tk.Menu(self.root)

        # Action menu
        action = tk.Menu(menubar, tearoff=0)
        action.add_command(label="Select Build Area",
                           command=self.select_build_area)
        action.add_separator()
        action.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="Action", menu=action)

        # Edit menu
        edit = tk.Menu(menubar, tearoff=0)
        edit.add_command(label="Reset", command=self.reset)
        menubar.add_cascade(label="Edit", menu=edit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About",
                "GR5 Vs GR6\nSelect a GR5 build and a GR6 build to compare.",
            ),
        )
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_panel(self):
        """Create the white panel with the buttons and dropdowns."""
        # White box floating in the middle of the gradient.
        self.panel = tk.Frame(self.canvas, bg="white", padx=6, pady=10)
        self.canvas_window = self.canvas.create_window(
            300, 200, window=self.panel, anchor="center"
        )

        # >>> MODIFY: font used for labels and buttons
        label_font = ("Georgia", 10, "bold")

        # --- "Select Build Area" button + the chosen path underneath ---
        self.btn_area = tk.Button(
            self.panel, text="Select Build Area", font=label_font,
            bg="#fffacd", relief="solid", bd=2,        # bg: button colour
            command=self.select_build_area,
        )
        self.btn_area.pack(pady=(0, 8))

        self.area_label = tk.Label(self.panel, text="(none selected)",
                                   bg="white", fg="#555", font=("Georgia", 8))
        self.area_label.pack()

        # --- Dropdown 1: Build Type (Release / Debug) ---
        self._label("Build Type", label_font)
        self.type_var = tk.StringVar()
        self.type_cb = ttk.Combobox(self.panel, textvariable=self.type_var,
                                    state="disabled", width=28)
        self.type_cb.pack()
        # Selecting a build type fills the GR5 / GR6 dropdowns.
        self.type_cb.bind("<<ComboboxSelected>>", self.on_type_selected)

        # --- Dropdown 2: GR5 build ---
        self._label("GR5 Build", label_font)
        self.gr5_var = tk.StringVar()
        self.gr5_cb = ttk.Combobox(self.panel, textvariable=self.gr5_var,
                                   state="disabled", width=28)
        self.gr5_cb.pack()

        # --- Dropdown 3: GR6 build ---
        self._label("GR6 Build", label_font)
        self.gr6_var = tk.StringVar()
        self.gr6_cb = ttk.Combobox(self.panel, textvariable=self.gr6_var,
                                   state="disabled", width=28)
        self.gr6_cb.pack()

        # --- RUN button ---
        self.btn_run = tk.Button(
            self.panel, text="RUN", font=label_font, bg="#ccff66",
            relief="solid", bd=2, width=6, command=self.run,
        )
        self.btn_run.pack(pady=(14, 0))

    def _label(self, text, font):
        """Small helper: a white label shown above a dropdown."""
        tk.Label(self.panel, text=text, font=font, bg="white").pack(pady=(8, 2))

    def draw_gradient(self):
        """Draw a vertical gradient on the canvas."""
        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 400)
        # >>> MODIFY: gradient colours (top -> bottom)
        color1 = "#eeaabf"  # light pink
        color2 = "#948be8"  # light purple

        # Remove the old gradient before redrawing (needed on resize).
        self.canvas.delete("gradient")

        # For each horizontal line, interpolate between color1 and color2.
        steps = height
        r1, g1, b1 = self.root.winfo_rgb(color1)
        r2, g2, b2 = self.root.winfo_rgb(color2)
        for i in range(steps):
            # winfo_rgb returns 16-bit values, so shift right by 8 to get
            # 8-bit values (0-255) after blending.
            r = int(r1 + (r2 - r1) * i / steps) >> 8
            g = int(g1 + (g2 - g1) * i / steps) >> 8
            b = int(b1 + (b2 - b1) * i / steps) >> 8
            hex_color = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)
            self.canvas.create_line(0, i, width, i,
                                    fill=hex_color, tags="gradient")

        # Keep the gradient behind the panel and keep the panel centred.
        self.canvas.tag_lower("gradient")
        self.canvas.coords(self.canvas_window, width // 2, height // 2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _subdirs(path):
        """Return a sorted list of the sub-folder names inside `path`.

        Files are ignored. Returns an empty list if the folder cannot be read.
        """
        try:
            return sorted(
                d for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))
            )
        except OSError:
            return []

    def reset(self):
        """Clear all selections and disable the dropdowns (Edit > Reset)."""
        for var in (self.type_var, self.gr5_var, self.gr6_var):
            var.set("")
        for cb in (self.type_cb, self.gr5_cb, self.gr6_cb):
            cb.config(values=[], state="disabled")
        self.build_root = None
        self.area_label.config(text="(none selected)")

    # ------------------------------------------------------------------
    # Actions (button / dropdown handlers)
    # ------------------------------------------------------------------
    def select_build_area(self):
        """Step 1: ask for the root folder and fill the Build Type dropdown."""
        self.log("Select Build Area clicked.")
        path = filedialog.askdirectory(title="Select Build Area",
                                       mustexist=True)
        if not path:                        # user pressed Cancel
            self.log("No folder selected.")
            return
        path = os.path.normpath(path)       # e.g. D:/Builds -> D:\Builds

        # The sub-folders of the root become the Build Type options.
        types = self._subdirs(path)
        if not types:
            self.log(f"WARNING: no sub-folders found in {path}")
            messagebox.showwarning("No builds",
                                   f"No sub-folders found in:\n{path}")
            return

        self.reset()
        self.build_root = path
        self.area_label.config(text=path)
        self.type_cb.config(values=types, state="readonly")
        self.log(f"Build area: {path}")
        self.log(f"Build types found: {', '.join(types)}")

    def on_type_selected(self, _event=None):
        """Step 2: a build type was chosen -> fill the GR5 / GR6 dropdowns."""
        type_path = os.path.join(self.build_root, self.type_var.get())
        builds = self._subdirs(type_path)
        self.log(f"Build type '{self.type_var.get()}' selected: "
                 f"{len(builds)} build(s) found.")
        self.log(f"Builds: {', '.join(builds) if builds else '(none)'}")

        # Clear any previous GR5 / GR6 choice and load the new list.
        # >>> MODIFY: if GR5 and GR6 should show different lists, build
        #     separate lists here instead of reusing `builds` for both.
        self.gr5_var.set("")
        self.gr6_var.set("")
        self.gr5_cb.config(values=builds, state="readonly")
        self.gr6_cb.config(values=builds, state="readonly")

    def run(self):
        """Step 3: RUN pressed -> build the two paths and verify them."""
        # --- Validate the selections ---
        if not self.build_root:
            messagebox.showwarning("Missing", "Select a build area first.")
            return

        build_type = self.type_var.get()    # e.g. "Release"
        gr5 = self.gr5_var.get()            # e.g. "Build_100"
        gr6 = self.gr6_var.get()            # e.g. "Build_102"
        if not (build_type and gr5 and gr6):
            messagebox.showwarning(
                "Missing", "Select build type, GR5 build and GR6 build.")
            return
        # Comparing a build with itself is allowed, but ask first.
        if gr5 == gr6:
            if not messagebox.askyesno(
                "Same build",
                "GR5 and GR6 are the same build. Continue anyway?",
            ):
                return

        # --- Construct the full paths ---
        # e.g. D:\Builds\Release\Build_100
        gr5_path = os.path.join(self.build_root, build_type, gr5)
        gr6_path = os.path.join(self.build_root, build_type, gr6)

        self.log("RUN clicked.")
        self.log(f"gr5_path = {gr5_path}")
        self.log(f"gr6_path = {gr6_path}")

        # --- Make sure both folders really exist ---
        for label, p in (("GR5", gr5_path), ("GR6", gr6_path)):
            if not os.path.isdir(p):
                self.log(f"ERROR: {label} path does not exist: {p}")
                messagebox.showerror("Path not found",
                                     f"{label} path does not exist:\n{p}")
                return

        self.log("Paths verified.")

        # >>> MODIFY: put your GR5 vs GR6 comparison / launch code here.
        #     Use gr5_path and gr6_path directly. Use self.log("...") or
        #     print("...") to report progress in the log box.

    def on_close(self):
        """Restore the real console and close the window."""
        self.log("Closing application.")
        sys.stdout, sys.stderr = self._orig_stdout, self._orig_stderr
        self.root.destroy()


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    GR5vsGR6App(root)
    root.mainloop()