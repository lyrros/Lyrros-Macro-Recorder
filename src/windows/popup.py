from sys import platform
from tkinter import Toplevel


class Popup(Toplevel):
    def __init__(self, name, w, h, parent):
        super().__init__(parent)
        self.title(name)
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        extra_width = 0
        extra_height = 0
        if platform.lower() == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            screensize = user32.GetSystemMetrics(0)
            user32 = ctypes.windll.user32
            dpi = user32.GetDpiForSystem()
            scaling_percentage = (dpi / 96) * 100
            if screensize > 2450 or scaling_percentage >= 125:
                extra_width = 110
                extra_height = 50
            if screensize > 3000 or scaling_percentage >= 125:
                extra_width = 200
                extra_height = 100
            if screensize > 3500 or scaling_percentage >= 125:
                extra_width = 200
                extra_height = 150
        self.geometry('%dx%d+%d+%d' % (w + extra_width, h + extra_height, x, y))
        self.resizable(False, False)
        if platform == "win32":
            self.attributes("-toolwindow", 1)
        elif platform == "darwin":
            # transient() groups this window with its parent, which made
            # title-bar dragging stutter on Tk 9.0. Without it the window
            # can open behind the main one, so raise it once it is mapped.
            self.after(50, self._raise_to_front)
        else:
            self.attributes("-topmost", 1)
        if platform != "darwin":
            # A local grab makes title-bar dragging stutter on macOS.
            self.grab_set()

    def _raise_to_front(self):
        try:
            if not self.winfo_exists():
                return
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(400, self._drop_topmost)
        except Exception:
            pass

    def _drop_topmost(self):
        try:
            if self.winfo_exists():
                self.attributes("-topmost", False)
        except Exception:
            pass
