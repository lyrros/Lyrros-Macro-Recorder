from tkinter import BOTH, END, LEFT, RIGHT, SINGLE, X, Y, Canvas, Frame as TkFrame, IntVar, Listbox
from tkinter.ttk import Button, Frame, Label, Radiobutton
from windows.popup import Popup


class AfterPlayBack(Popup):
    def __init__(self, parent, main_app):
        tc = main_app.text_content["options_menu"]["settings_menu"]["after_playback_settings"]
        super().__init__(tc["title"], 470, 405, parent)
        self.resizable(False, False)
        main_app.prevent_record = True
        self.settings = main_app.settings

        ap_cfg = self.settings.settings_dict.setdefault("After_Playback", {"Mode": "Idle"})
        cur_mode = ap_cfg.get("Mode", "Idle")
        if "hibernate" in cur_mode.lower():
            cur_mode = "Standby"
        self.delay_var = IntVar(value=int(ap_cfg.get("Delay", 0)))

        Label(self, text=tc["title"], font=("Helvetica Neue", 15, "bold")).pack(pady=(14, 2))
        Label(self, text=tc.get("when_playback_complete_text", "Choose what happens automatically when playback finishes"), font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 10))

        btns = Frame(self)
        btns.pack(side="bottom", pady=(8, 14))
        Button(btns, text=main_app.text_content["global"]["confirm_button"], width=12, command=self._save).pack(side="left", padx=6)
        Button(btns, text=main_app.text_content["global"]["cancel_button"], width=12, command=self.destroy).pack(side="left", padx=6)

        delay_row = Frame(self)
        delay_row.pack(side="bottom", fill=X, padx=24, pady=(8, 4))
        Label(delay_row, text="Countdown Delay:", font=("Helvetica Neue", 11, "bold"), foreground="#40C4FF").pack(side="left", padx=(0, 8))
        for sec in (0, 3, 5, 10, 30):
            Radiobutton(delay_row, text="Now" if sec == 0 else f"{sec}s", variable=self.delay_var, value=sec).pack(side="left", padx=4)

        self.actions = [
            ("Idle", f"{tc.get('idle', 'Do Nothing (Idle)')}  —  Keep app open and ready"),
            ("Quit software", f"{tc.get('quit_software', 'Quit Macro Recorder')}  —  Close app when playback ends"),
            ("Standby", f"{tc.get('standby', 'Sleep Mac')}  —  Put Mac into low-power sleep mode"),
            ("Log off computer", f"{tc.get('log_off_computer', 'Log Out of macOS')}  —  Sign out of current macOS session"),
            ("Restart computer", f"{tc.get('restart computer', 'Restart Mac')}  —  Reboot Mac via System Events"),
            ("Turn off computer", f"{tc.get('turn_off_computer', 'Shut Down Mac')}  —  Power off Mac safely"),
        ]

        border = TkFrame(self, bg="#3c3c3c", padx=1, pady=1)
        border.pack(fill=BOTH, expand=True, padx=24)
        wrap = Frame(border)
        wrap.pack(fill=BOTH, expand=True)

        sb = Canvas(wrap, width=10, height=1, bg="#262626", highlightthickness=0, bd=0)
        sb.pack(side=RIGHT, fill=Y)

        def _upd_sb(lo, hi):
            sb.delete("all")
            lo, hi = float(lo), float(hi)
            h = max(1, sb.winfo_height())
            y1 = max(2, int(lo * h) + 2)
            y2 = min(h - 2, max(y1 + 18, int(hi * h) - 2))
            sb.create_rectangle(2, y1, 8, y2, fill="#5c5c5c", outline="")

        self.lb = Listbox(wrap, yscrollcommand=_upd_sb, selectmode=SINGLE, activestyle="none", bg="#1e1e1e", fg="#e0e0e0", selectbackground="#2b5b84", selectforeground="#ffffff", font=("Helvetica Neue", 12), highlightthickness=0, bd=0, height=4)
        self.lb.pack(side=LEFT, fill=BOTH, expand=True)
        sb.bind("<Configure>", lambda e: _upd_sb(*self.lb.yview()))
        sb.bind("<B1-Motion>", lambda e: self.lb.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))
        sb.bind("<Button-1>", lambda e: self.lb.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))

        sel_idx = 0
        for idx, (mode_val, label_txt) in enumerate(self.actions):
            self.lb.insert(END, f"  {label_txt}")
            if mode_val == cur_mode:
                sel_idx = idx
        self.lb.selection_set(sel_idx)
        self.lb.see(sel_idx)

        self.wait_window()
        main_app.prevent_record = False

    def _save(self):
        sel = self.lb.curselection()
        chosen = self.actions[sel[0]][0] if sel else "Idle"
        self.settings.change_settings("After_Playback", "Mode", None, chosen)
        self.settings.settings_dict.setdefault("After_Playback", {})["Delay"] = int(self.delay_var.get())
        try:
            self.settings.save_settings()
        except Exception:
            pass
        self.destroy()
