import os
import atexit
import string
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ============================================================
# Configuration
# ============================================================

BEYOND_COMPARE = r"C:\Program Files\Beyond Compare 5\BComp.exe"

mapped_drives = []

# ============================================================
# Drive Mapping Functions
# ============================================================

def get_free_drive_letter():
    for letter in reversed(string.ascii_uppercase):
        drive = f"{letter}:\\"

        if not os.path.exists(drive):
            return f"{letter}:"

    raise RuntimeError("No free drive letter available")


def map_drive(folder_path):
    drive = get_free_drive_letter()

    subprocess.check_call([
        "subst",
        drive,
        folder_path
    ])

    mapped_drives.append(drive)

    return drive


def cleanup_drives():

    for drive in mapped_drives[:]:

        try:
            subprocess.call([
                "subst",
                drive,
                "/d"
            ])
        except Exception:
            pass

    mapped_drives.clear()


atexit.register(cleanup_drives)

# ============================================================
# Folder Functions
# ============================================================

def get_folders(path):

    if not os.path.isdir(path):
        return []

    try:
        return sorted(
            [
                name
                for name in os.listdir(path)
                if os.path.isdir(os.path.join(path, name))
            ]
        )
    except Exception:
        return []


def browse_root(entry, build_combo):

    path = filedialog.askdirectory()

    if not path:
        return

    entry.delete(0, tk.END)
    entry.insert(0, path)

    folders = get_folders(path)

    build_combo["values"] = folders

    if folders:
        build_combo.current(0)


# ============================================================
# Build Selection Events
# ============================================================

def build1_selected(event=None):

    root_path = root1_entry.get()
    build = build1_combo.get()

    path = os.path.join(root_path, build)

    subfolders = get_folders(path)

    sub1_combo["values"] = subfolders

    if subfolders:
        sub1_combo.current(0)


def build2_selected(event=None):

    root_path = root2_entry.get()
    build = build2_combo.get()

    path = os.path.join(root_path, build)

    subfolders = get_folders(path)

    sub2_combo["values"] = subfolders

    if subfolders:
        sub2_combo.current(0)


# ============================================================
# Compare
# ============================================================

def compare():

    try:

        path1 = os.path.join(
            root1_entry.get(),
            build1_combo.get(),
            sub1_combo.get()
        )

        path2 = os.path.join(
            root2_entry.get(),
            build2_combo.get(),
            sub2_combo.get()
        )

        if not os.path.isdir(path1):
            raise Exception("Build 1 path not found")

        if not os.path.isdir(path2):
            raise Exception("Build 2 path not found")

        drive1 = map_drive(path1)
        drive2 = map_drive(path2)

        subprocess.Popen([
            BEYOND_COMPARE,
            drive1 + "\\",
            drive2 + "\\"
        ])

        status_var.set(
            f"Mapped {path1} -> {drive1} | {path2} -> {drive2}"
        )

    except Exception as ex:

        messagebox.showerror(
            "Error",
            str(ex)
        )


# ============================================================
# Exit Handling
# ============================================================

def on_close():

    cleanup_drives()

    root.destroy()


# ============================================================
# GUI
# ============================================================

root = tk.Tk()
root.title("Build Comparison Tool")
root.geometry("950x350")

# ------------------------------------------------------------
# Build Root 1
# ------------------------------------------------------------

frame1 = ttk.LabelFrame(root, text="Build 1")
frame1.pack(fill="x", padx=10, pady=10)

root1_entry = ttk.Entry(frame1, width=100)
root1_entry.grid(row=0, column=0, padx=5, pady=5)

ttk.Button(
    frame1,
    text="Browse",
    command=lambda: browse_root(root1_entry, build1_combo)
).grid(row=0, column=1, padx=5)

ttk.Label(frame1, text="Folder").grid(
    row=1,
    column=0,
    sticky="w",
    padx=5
)

build1_combo = ttk.Combobox(
    frame1,
    width=80,
    state="readonly"
)
build1_combo.grid(row=2, column=0, padx=5, pady=5)
build1_combo.bind(
    "<<ComboboxSelected>>",
    build1_selected
)

ttk.Label(frame1, text="Sub Folder").grid(
    row=3,
    column=0,
    sticky="w",
    padx=5
)

sub1_combo = ttk.Combobox(
    frame1,
    width=80,
    state="readonly"
)
sub1_combo.grid(row=4, column=0, padx=5, pady=5)

# ------------------------------------------------------------
# Build Root 2
# ------------------------------------------------------------

frame2 = ttk.LabelFrame(root, text="Build 2")
frame2.pack(fill="x", padx=10, pady=10)

root2_entry = ttk.Entry(frame2, width=100)
root2_entry.grid(row=0, column=0, padx=5, pady=5)

ttk.Button(
    frame2,
    text="Browse",
    command=lambda: browse_root(root2_entry, build2_combo)
).grid(row=0, column=1, padx=5)

ttk.Label(frame2, text="Folder").grid(
    row=1,
    column=0,
    sticky="w",
    padx=5
)

build2_combo = ttk.Combobox(
    frame2,
    width=80,
    state="readonly"
)
build2_combo.grid(row=2, column=0, padx=5, pady=5)
build2_combo.bind(
    "<<ComboboxSelected>>",
    build2_selected
)

ttk.Label(frame2, text="Sub Folder").grid(
    row=3,
    column=0,
    sticky="w",
    padx=5
)

sub2_combo = ttk.Combobox(
    frame2,
    width=80,
    state="readonly"
)
sub2_combo.grid(row=4, column=0, padx=5, pady=5)

# ------------------------------------------------------------
# Compare Button
# ------------------------------------------------------------

ttk.Button(
    root,
    text="Compare",
    command=compare
).pack(pady=10)

status_var = tk.StringVar()
status_var.set("Ready")

ttk.Label(
    root,
    textvariable=status_var
).pack()

root.protocol(
    "WM_DELETE_WINDOW",
    on_close
)

root.mainloop()