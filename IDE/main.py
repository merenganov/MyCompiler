import tkinter as tk
from ui.ide_window import IDEWindow

def main():
    root = tk.Tk()
    IDEWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()