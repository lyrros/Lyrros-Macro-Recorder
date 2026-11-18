from tkinter import StringVar, Entry as TkEntry
from tkinter.ttk import Frame, Label, Button
from windows.popup import Popup

class Speed(Popup):
    def __init__(self, parent, main_app):
        super().__init__("Playback Speed", 530, 260, parent)
        self.resizable(True, True)
        self.main_app = main_app
        cur = main_app.settings.settings_dict["Playback"]["Speed"]
        Label(self, text="Playback Speed", font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        Label(self, text="Choose a speed preset or click 'Advanced' for custom values", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 12))
        self.var = StringVar(value=f"{float(cur):g}")
        presets = Frame(self)
        presets.pack(padx=18, pady=(0, 8))
        for label, val in [("0.5x (Slower)", "0.5"), ("1x (Normal)", "1"), ("2x (Faster)", "2"), ("5x (Fastest)", "5")]:
            Button(presets, text=label, command=lambda v=val: self.var.set(v)).pack(side="left", padx=4)
        self.desc_lbl = Label(self, text="", font=("Helvetica Neue", 11, "bold"), foreground="#40C4FF")
        self.desc_lbl.pack(pady=(2, 10))
        self.adv_open = False
        self.adv_btn = Button(self, text="Advanced ▸", width=12, command=self._toggle_adv)
        self.adv_btn.pack(pady=(0, 10))
        self.adv_frame = Frame(self)
        Label(self.adv_frame, text="Custom Speed (0.1x – 10x)  •  Higher = Faster", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(4, 6))
        self.ent = TkEntry(self.adv_frame, textvariable=self.var, width=8, justify="center", font=("Helvetica Neue", 14), bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff", relief="flat", bd=0, highlightthickness=1, highlightbackground="#454545", highlightcolor="#40C4FF")
        self.ent.pack(ipady=4)
        self.ent.bind("<Return>", lambda e: self.focus_set())
        self.ent.bind("<Button-1>", lambda e: (self.ent.focus_force(), self.ent.after(10, lambda: (self.ent.select_range(0, "end"), self.ent.icursor("end")))))
        self.ent.bind("<FocusIn>", lambda e: self.ent.after(10, lambda: (self.ent.select_range(0, "end"), self.ent.icursor("end"))))
        self.ent.bind("<FocusOut>", lambda e: self.ent.select_clear())
        self.bind("<Button-1>", lambda e: self.focus_set() if e.widget != self.ent else None)
        self.var.trace_add("write", lambda *_: self._update_desc())
        self._update_desc()
        self.btns = Frame(self)
        self.btns.pack(side="bottom", pady=(6, 14))
        Button(self.btns, text="Reset to Default", width=14, command=self._confirm_reset).pack(side="left", padx=6)
        Button(self.btns, text="Confirm", width=10, command=self._save).pack(side="left", padx=6)
        Button(self.btns, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=6)

    def _toggle_adv(self):
        self.adv_open = not self.adv_open
        self.adv_btn.config(text="Advanced ▾" if self.adv_open else "Advanced ▸")
        self.adv_frame.pack(before=self.btns, pady=(2, 8)) if self.adv_open else self.adv_frame.pack_forget()
        self.geometry(f"530x{335 if self.adv_open else 260}")

    def _update_desc(self):
        try:
            v = float(self.var.get().strip())
            if v == 1.0:
                self.desc_lbl.config(text="Selected: 1x  •  Normal recorded speed (100% duration)", foreground="#4CAF50")
            elif 1.0 < v <= 10:
                self.desc_lbl.config(text=f"Selected: {v:g}x faster  •  Takes {round(100 / v)}% of original time", foreground="#40C4FF")
            elif 0.1 <= v < 1.0:
                self.desc_lbl.config(text=f"Selected: {v:g}x slower  •  Takes {round(1 / v, 1):g}x longer", foreground="#FFB74D")
            else:
                self.desc_lbl.config(text="Enter a number between 0.1 and 10", foreground="#FF5252")
        except ValueError:
            self.desc_lbl.config(text="Enter a valid speed number", foreground="#FF5252")

    def _confirm_reset(self):
        dlg = Popup("Confirm Reset", 340, 155, self)
        Label(dlg, text="Reset Playback Speed?", font=("Helvetica Neue", 14, "bold")).pack(pady=(18, 4))
        Label(dlg, text="Restore speed back to default (1x Normal)?", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 16))
        row = Frame(dlg)
        row.pack()
        Button(row, text="Reset", width=10, command=lambda: (self.var.set("1"), dlg.destroy())).pack(side="left", padx=6)
        Button(row, text="Cancel", width=10, command=dlg.destroy).pack(side="left", padx=6)

    def _save(self):
        try:
            val = float(self.var.get().strip())
            if 0.1 <= val <= 10:
                self.main_app.settings.change_settings("Playback", "Speed", None, val)
                self.destroy()
        except ValueError:
            pass
