import copy
from tkinter import Frame as TkFrame, Label as TkLabel
from tkinter.ttk import Frame, Label, Button
from utils.keys import vk_nb
from windows.popup import Popup

class Hotkeys(Popup):
    def __init__(self, parent, main_app):
        super().__init__("Hotkeys", 475, 355, parent)
        main_app.prevent_record = True
        cfg = main_app.settings.settings_dict
        mgr = main_app.hotkeyManager
        Label(self, text="Keyboard Shortcuts", font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        Label(self, text="Click 'Set' and press your desired key combination", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 14))
        rows = [
            ("Start Record", "Record_Start", 0),
            ("Stop Record", "Record_Stop", 1),
            ("Start Playback", "Playback_Start", 2),
            ("Stop Playback", "Playback_Stop", 3),
        ]
        box = Frame(self)
        box.pack(padx=24, fill="x")
        box.columnconfigure(1, weight=1)
        for r, (title, kname, idx) in enumerate(rows):
            raw = copy.deepcopy(cfg["Hotkeys"][kname])
            parts = []
            for k in raw:
                c = k.replace("<63>", "Fn").replace("<179>", "Fn").replace("Key.", "").replace("_l", "").replace("_r", "").replace("_gr", "")
                if "<" in c and ">" in c and c in vk_nb:
                    c = vk_nb[c]
                parts.append(c.upper())
            disp = " + ".join(parts) if parts else "None"
            Label(box, text=title, font=("Helvetica Neue", 12, "bold"), foreground="#e0e0e0").grid(row=r, column=0, sticky="w", pady=6)
            badge = TkFrame(box, bg="#2a2a2a", highlightthickness=1, highlightbackground="#454545")
            badge.grid(row=r, column=1, sticky="ew", padx=14, pady=6)
            lbl = TkLabel(badge, text=disp, font=("Helvetica Neue", 12, "bold"), bg="#2a2a2a", fg="#40C4FF", pady=4)
            lbl.pack(fill="x")
            btns = Frame(box)
            btns.grid(row=r, column=2, sticky="w", pady=6)
            Button(btns, text="Set", width=5, command=lambda k=kname, l=lbl, i=idx: mgr.enable_hot_key_detection(k, l, i)).pack(side="left", padx=(0, 4))
            Button(btns, text="Clear", width=5, command=lambda k=kname, l=lbl: self._clear(mgr, k, l)).pack(side="left")
        Button(self, text="Done", width=11, command=self.destroy).pack(pady=(16, 14))
        self.wait_window()
        main_app.prevent_record = False
        if hasattr(main_app, "hk_lbl"):
            h = main_app.settings.settings_dict["Hotkeys"]
            fmt = lambda a: "+".join(x.replace("<63>", "Fn").replace("<179>", "Fn").replace("Key.", "").upper() for x in a) if a else "None"
            main_app.hk_lbl.config(text=f"Start Rec: {fmt(h['Record_Start'])}  |  Stop Rec: {fmt(h['Record_Stop'])}  |  Play: {fmt(h['Playback_Start'])}  |  Stop: {fmt(h['Playback_Stop'])}")

    def _clear(self, mgr, kname, lbl):
        mgr.clear_hot_key(kname, lbl)
        lbl.config(text="None")
