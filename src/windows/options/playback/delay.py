from tkinter import StringVar, Entry as TkEntry
from tkinter.ttk import Frame, Label, Button
from windows.popup import Popup

class Delay(Popup):
    def __init__(self, parent, main_app):
        super().__init__("Loop Delay", 530, 260, parent)
        self.resizable(True, True)
        self.main_app = main_app
        cur = main_app.settings.settings_dict["Playback"]["Repeat"]["Delay"]
        Label(self, text="Delay Between Loops", font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        Label(self, text="Choose a pause preset or click 'Advanced' for custom seconds", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 12))
        self.var = StringVar(value=f"{float(cur):g}")
        presets = Frame(self)
        presets.pack(padx=18, pady=(0, 8))
        for label, val in [("0s (None)", "0"), ("0.5s (Half sec)", "0.5"), ("1s (1 sec)", "1"), ("5s (5 secs)", "5")]:
            Button(presets, text=label, command=lambda v=val: self.var.set(v)).pack(side="left", padx=4)
        self.desc_lbl = Label(self, text="", font=("Helvetica Neue", 11, "bold"), foreground="#40C4FF")
        self.desc_lbl.pack(pady=(2, 10))
        self.adv_open = False
        self.adv_btn = Button(self, text="Advanced ▸", width=12, command=self._toggle_adv)
        self.adv_btn.pack(pady=(0, 10))
        self.adv_frame = Frame(self)
        Label(self.adv_frame, text="Custom Pause (Seconds)  •  Wait between each loop", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(4, 6))
        ent_row = Frame(self.adv_frame)
        ent_row.pack()
        self.ent = TkEntry(ent_row, textvariable=self.var, width=8, justify="center", font=("Helvetica Neue", 14), bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff", relief="flat", bd=0, highlightthickness=1, highlightbackground="#454545", highlightcolor="#40C4FF")
        self.ent.pack(side="left", ipady=4)
        self.ent.bind("<Return>", lambda e: self.focus_set())
        self.ent.bind("<Button-1>", lambda e: (self.ent.focus_force(), self.ent.after(10, lambda: (self.ent.select_range(0, "end"), self.ent.icursor("end")))))
        self.ent.bind("<FocusIn>", lambda e: self.ent.after(10, lambda: (self.ent.select_range(0, "end"), self.ent.icursor("end"))))
        self.ent.bind("<FocusOut>", lambda e: self.ent.select_clear())
        self.bind("<Button-1>", lambda e: self.focus_set() if e.widget != self.ent else None)
        self.conv_lbl = Label(ent_row, text="", font=("Helvetica Neue", 12, "bold"), foreground="#40C4FF")
        self.conv_lbl.pack(side="left")
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
            if v >= 60:
                rem = v
                days = int(rem // 86400); rem %= 86400
                hours = int(rem // 3600); rem %= 3600
                mins = int(rem // 60)
                secs = round(rem % 60, 2)
                parts = []
                if days > 0: parts.append(f"{days} day" if days == 1 else f"{days} days")
                if hours > 0: parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")
                if mins > 0: parts.append(f"{mins} minute" if mins == 1 else f"{mins} minutes")
                if secs > 0: parts.append(f"{secs:g} second" if secs == 1 else f"{secs:g} seconds")
                formatted = parts[0] if len(parts) == 1 else (", ".join(parts[:-1]) + " and " + parts[-1])
                self.conv_lbl.config(text=f"  = {formatted}")
                self.conv_lbl.pack(side="left")
            else:
                self.conv_lbl.pack_forget()
            if v == 0:
                self.desc_lbl.config(text="Selected: 0s  •  No pause between loops", foreground="#4CAF50")
            elif v > 0:
                unit = "second" if v == 1 else "seconds"
                self.desc_lbl.config(text=f"Selected: {v:g} {unit} pause before next loop", foreground="#40C4FF")
            else:
                self.desc_lbl.config(text="Enter 0 or a positive number of seconds", foreground="#FF5252")
        except ValueError:
            self.conv_lbl.pack_forget()
            self.desc_lbl.config(text="Enter a valid number of seconds", foreground="#FF5252")

    def _confirm_reset(self):
        dlg = Popup("Confirm Reset", 340, 155, self)
        Label(dlg, text="Reset Loop Delay?", font=("Helvetica Neue", 14, "bold")).pack(pady=(18, 4))
        Label(dlg, text="Restore pause between loops to default (0s)?", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 16))
        row = Frame(dlg)
        row.pack()
        Button(row, text="Reset", width=10, command=lambda: (self.var.set("0"), dlg.destroy())).pack(side="left", padx=6)
        Button(row, text="Cancel", width=10, command=dlg.destroy).pack(side="left", padx=6)

    def _save(self):
        try:
            val = float(self.var.get().strip())
            if val >= 0:
                self.main_app.settings.change_settings("Playback", "Repeat", "Delay", val)
                self.destroy()
        except ValueError:
            pass
