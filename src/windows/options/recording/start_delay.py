from tkinter import IntVar, Spinbox, W, X, LEFT, RIGHT
from tkinter.ttk import Button, Frame, Label
from windows.popup import Popup

class StartDelay(Popup):
    def __init__(self, parent, main_app):
        super().__init__("Recording Start Delay", 330, 165, parent)
        self.main_app = main_app
        cur = int(self.main_app.settings.settings_dict.setdefault("Recordings", {}).get("Start_Delay", 0) or 0)
        body = Frame(self); body.pack(fill=X, padx=18, pady=(16, 10))
        Label(body, text="Delay before recording starts (seconds):", font=("Helvetica Neue", 12)).pack(anchor=W, pady=(0, 8))
        row = Frame(body); row.pack(fill=X)
        self.delay_var = IntVar(value=cur)
        Spinbox(row, from_=0, to=60, textvariable=self.delay_var, width=8, font=("Helvetica Neue", 12)).pack(side=LEFT)
        Label(row, text="sec  (0 = instant start)", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(side=LEFT, padx=(10, 0))
        btns = Frame(self); btns.pack(fill=X, padx=18, pady=(8, 12))
        Button(btns, text="Cancel", width=9, command=self.destroy).pack(side=RIGHT, padx=(6, 0))
        Button(btns, text="Save", width=9, command=self._save).pack(side=RIGHT)

    def _save(self):
        try:
            val = max(0, min(60, int(self.delay_var.get())))
        except Exception:
            val = 0
        self.main_app.settings.settings_dict.setdefault("Recordings", {})["Start_Delay"] = val
        self.main_app.settings.save_settings()
        self.main_app.status_text.configure(text=f"Recording start delay set to {val}s")
        self.destroy()
