import tkinter as tk
from tkinter import ttk

from ui.ide_window import IDEWindow


THEMES = {
    "dark": {
        "BG": "#1e1e1e",
        "PANEL": "#252526",
        "BTN": "#2d2d2d",
        "FG": "#d4d4d4",
        "FG_DIM": "#a0a0a0",
        "ACCENT": "#264f78",
    },
    "light": {
        "BG": "#f3f3f3",
        "PANEL": "#e6e6e6",
        "BTN": "#f0f0f0",
        "FG": "#111111",
        "FG_DIM": "#444444",
        "ACCENT": "#cce6ff",
    },
}


def apply_theme(root: tk.Tk, mode: str) -> None:
    cfg = THEMES[mode]
    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    BG = cfg["BG"]
    PANEL = cfg["PANEL"]
    BTN = cfg["BTN"]
    FG = cfg["FG"]
    FG_DIM = cfg["FG_DIM"]
    ACCENT = cfg["ACCENT"]

    style.configure(".", background=BG, foreground=FG)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("TSeparator", background=BG)

    style.configure("TButton", background=BTN, foreground=FG, padding=(8, 4))
    style.map(
        "TButton",
        background=[("active", "#3e3e3e" if mode == "dark" else "#e0e0e0"),
                    ("pressed", "#3a3a3a" if mode == "dark" else "#d8d8d8")],
        foreground=[("disabled", FG_DIM)],
    )

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=BTN, foreground=FG, padding=(10, 6))
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG),
                    ("active", "#3a3a3a" if mode == "dark" else "#e8e8e8")],
        foreground=[("selected", "#ffffff" if mode == "dark" else "#000000")],
    )

    style.configure("TPanedwindow", background=BG)

    style.configure(
        "Treeview",
        background=PANEL,
        foreground=FG,
        fieldbackground=PANEL,
        borderwidth=0,
        rowheight=24,
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff" if mode == "dark" else "#000000")],
    )

    style.configure("TScrollbar", background=BG, troughcolor=PANEL, borderwidth=0)


def main():
    root = tk.Tk()

    # Default: dark
    apply_theme(root, "dark")

    # Pasamos callback y themes al IDEWindow
    IDEWindow(root, apply_theme_callback=lambda mode: apply_theme(root, mode), default_theme="dark")
    root.mainloop()


if __name__ == "__main__":
    main()