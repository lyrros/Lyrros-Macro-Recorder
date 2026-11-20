import copy, json
import sys
from json import load
from os import path
from time import time
from tkinter import (
    BOTH, BOTTOM, DISABLED, END, LEFT, NORMAL, RIGHT, X, Y,
    BooleanVar, Canvas, Entry as TkEntry, Frame as TkFrame,
    Label as TkLabel, Listbox, PhotoImage, StringVar, W
)
from tkinter.ttk import Button, Checkbutton, Frame, Label
from PIL import Image
from pystray import Icon, MenuItem

from hotkeys.hotkeys_manager import HotkeysManager
from macro import Macro
from utils.get_file import resource_path
from utils.key_names import format_key_name
from utils.record_file_management import RecordFileManagement
from utils.startup_record import get_startup_record_path
from utils.user_settings import UserSettings
from utils.version import Version
from windows.main.menu_bar import MenuBar
from windows.others.step_editor import STEP_TYPE_LABELS
from windows.others.new_ver_avalaible import NewVerAvailable
from windows.window import Window


class MainApp(Window):
    def __init__(self):
        super().__init__("Lyrro's Macro Recorder", 700, 490)
        self.resizable(True, True)
        self.settings = UserSettings(self)
        self._permissions_popup_open = False
        self._permissions_popup_pending = False
        self.macos_im_permission_missing_at_launch = False
        self.macos_post_permission_missing_at_launch = False
        if sys.platform == "darwin":
            from windows.others.permissions_popup import check_macos_permissions

            im_ok, post_ok = check_macos_permissions()
            self.macos_im_permission_missing_at_launch = not im_ok
            self.macos_post_permission_missing_at_launch = not post_ok
        self.load_language()
        self.version = Version(self.settings.settings_dict, self)
        self.menu = MenuBar(self)
        self.macro = Macro(self)
        self.hotkeyManager = HotkeysManager(self)
        from windows.menu_bar_status import MenuBarStatus
        self.menu_bar_status = MenuBarStatus(self)
        self._playback_started = None
        self.current_file = None
        self.macro_recorded = False
        self.macro_saved = False
        self.prevent_record = False

        top_bar = Frame(self)
        top_bar.pack(fill=X, padx=12, pady=(7, 2))
        self.status_badge = Label(top_bar, text="● READY", font=("Helvetica Neue", 13, "bold"), foreground="#4CAF50")
        self.status_badge.pack(side=LEFT)

        self.pin_var = BooleanVar(value=False)
        Checkbutton(top_bar, text="Pin on Top", variable=self.pin_var, onvalue=True, offvalue=False, command=lambda: self.attributes("-topmost", 1 if self.pin_var.get() else 0)).pack(side=RIGHT)
        self.file_lbl = Label(top_bar, text="Loaded: None", font=("Helvetica Neue", 12), foreground="#cccccc")
        self.file_lbl.pack(side=RIGHT, padx=(0, 14))

        info_bar = Frame(self)
        info_bar.pack(fill=X, padx=12, pady=(0, 3))
        self.coord_lbl = Label(info_bar, text="Cursor: X=0 Y=0", font=("Helvetica Neue", 13))
        self.coord_lbl.pack(side=LEFT)

        rep_box = Frame(info_bar)
        rep_box.pack(side=RIGHT)
        rep_col = Frame(rep_box)
        rep_col.pack(side=LEFT, anchor="n")
        rep_top = Frame(rep_col)
        rep_top.pack(side="top", anchor="w")
        self.loop_lbl = Label(rep_top, text="Loops:", font=("Helvetica Neue", 13), foreground="#cccccc")
        self.loop_lbl.pack(side=LEFT, padx=(0, 8))
        rep_cfg = self.settings.settings_dict["Playback"]["Repeat"]
        self.inf_var = BooleanVar(value=rep_cfg.get("Infinite", False))
        self.rep_var = StringVar(value=str(max(1, rep_cfg.get("Times", 1))))
        self.rep_entry = TkEntry(rep_top, textvariable=self.rep_var, width=4, justify="center", font=("Helvetica Neue", 12), bg="#2a2a2a", fg="#f0f0f0", disabledbackground="#1e1e1e", disabledforeground="#666666", insertbackground="#ffffff", relief="flat", bd=0, highlightthickness=1, highlightbackground="#454545", highlightcolor="#40C4FF")
        self.rep_entry.pack(side=LEFT, ipady=3, padx=(0, 8))
        self.rep_entry.bind("<Return>", lambda e: (self._apply_inline_repeat(), self.focus_set()))
        self.rep_entry.bind("<Button-1>", lambda e: (self.rep_entry.focus_force(), self.rep_entry.after(10, lambda: (self.rep_entry.select_range(0, "end"), self.rep_entry.icursor("end")))) if not self.inf_var.get() else "break")
        self.rep_entry.bind("<FocusOut>", lambda e: self.rep_entry.select_clear())
        self.bind("<Button-1>", lambda e: self.focus_set() if e.widget != self.rep_entry else None)
        Checkbutton(rep_col, text="Infinite (∞)", variable=self.inf_var, onvalue=True, offvalue=False, command=self._toggle_infinite).pack(side="top", anchor="w", pady=(4, 0))
        Button(rep_box, text="Apply", width=5, command=self._apply_inline_repeat).pack(side=LEFT, anchor="n")
        self._toggle_infinite(save=False)

        bottom_bar = Frame(self)
        bottom_bar.pack(side=BOTTOM, fill=X)
        self.status_text = Label(bottom_bar, text="Ready", relief="flat", anchor=W, padding=(10, 4), font=("Helvetica Neue", 11), foreground="#b0b0b0")
        self.status_text.pack(side=LEFT, fill=X, expand=True)
        ver_lbl = Label(bottom_bar, text="v1.0.9", relief="flat", anchor="e", padding=(10, 4), font=("Helvetica Neue", 11, "bold"), foreground="#8e8e8e", cursor="pointinghand")
        ver_lbl.pack(side=RIGHT)

        self.playImg = PhotoImage(file=resource_path(path.join("assets", "button", "play.png")))
        self.recordImg = PhotoImage(file=resource_path(path.join("assets", "button", "record.png")))
        self.stopImg = PhotoImage(file=resource_path(path.join("assets", "button", "stop.png")))
        self.center_frame = Frame(self)
        self.center_frame.pack(pady=2)

        class FramedIconBtn:
            def __init__(btn, parent, image, default_text, command=None, state="normal"):
                btn.card = TkFrame(parent, bg="#2a2a2a", highlightthickness=1, highlightbackground="#454545", padx=18, pady=6, cursor="pointinghand")
                btn.icon_lbl = TkLabel(btn.card, image=image, bg="#2a2a2a", cursor="pointinghand")
                btn.icon_lbl.pack()
                btn.txt_lbl = TkLabel(btn.card, text=default_text, font=("Helvetica Neue", 11, "bold"), bg="#2a2a2a", fg="#e0e0e0", cursor="pointinghand")
                btn.txt_lbl.pack(pady=(4, 0))
                btn._default_text = default_text
                btn._cmd = command
                btn._state = state
                for w in (btn.card, btn.icon_lbl, btn.txt_lbl):
                    w.bind("<Button-1>", btn._on_click)
                    w.bind("<Enter>", lambda e: btn._hover(True))
                    w.bind("<Leave>", lambda e: btn._hover(False))
                btn._apply_state()

            def _hover(btn, inside):
                if btn._state == "disabled":
                    return
                bg = "#353535" if inside else "#2a2a2a"
                bd = "#666666" if inside else "#454545"
                for w in (btn.card, btn.icon_lbl, btn.txt_lbl):
                    w.config(bg=bg)
                btn.card.config(highlightbackground=bd)

            def _on_click(btn, _e):
                if btn._state != "disabled" and btn._cmd:
                    btn._cmd()

            def _apply_state(btn):
                dis = (btn._state == "disabled")
                bg = "#222222" if dis else "#2a2a2a"
                fg = "#666666" if dis else "#e0e0e0"
                for w in (btn.card, btn.icon_lbl, btn.txt_lbl):
                    w.config(bg=bg)
                btn.card.config(highlightbackground="#333333" if dis else "#454545")
                btn.txt_lbl.config(fg=fg)

            def configure(btn, **kw):
                if "image" in kw:
                    img = kw["image"]
                    btn.icon_lbl.config(image=img)
                    if img == self.stopImg:
                        btn.txt_lbl.config(text="Stop", fg="#FF5252")
                    else:
                        btn.txt_lbl.config(text=btn._default_text, fg="#e0e0e0" if btn._state != "disabled" else "#666666")
                if "command" in kw:
                    btn._cmd = kw["command"]
                if "state" in kw:
                    btn._state = str(kw["state"]).lower()
                    btn._apply_state()
            config = configure

            def pack(btn, **kw):
                btn.card.pack(**kw)

        startup_record = get_startup_record_path()
        if startup_record:
            with open(startup_record, "r") as record:
                loaded_content = load(record)
            self.macro.import_record(loaded_content)
            self.playBtn = FramedIconBtn(self.center_frame, self.playImg, "Play", command=self.macro.start_playback, state="normal")
            self.macro_recorded = True
            self.macro_saved = True
        else:
            self.playBtn = FramedIconBtn(self.center_frame, self.playImg, "Play", state="disabled")
        self.playBtn.pack(side=LEFT, padx=24)

        self.recordBtn = FramedIconBtn(self.center_frame, self.recordImg, "Record", command=self.macro.start_record, state="normal")
        self.recordBtn.pack(side=LEFT, padx=24)

        record_management = RecordFileManagement(self, self.menu)
        self.bind("<Control-Shift-S>", record_management.save_macro_as)

        list_hdr = Frame(self)
        list_hdr.pack(fill=X, padx=14, pady=(6, 2))
        list_title_row = Frame(list_hdr)
        list_title_row.pack(fill=X)
        self.steps_lbl = Label(list_title_row, text="Recorded Actions (0 steps):", font=("Helvetica Neue", 13, "bold"))
        self.steps_lbl.pack(side=LEFT)
        step_toolbar = Frame(list_hdr)
        step_toolbar.pack(pady=(3, 0))
        Button(step_toolbar, text="Clear", width=6, command=self._clear_macro).pack(side=LEFT, padx=(0, 4))
        Button(step_toolbar, text="↑", width=2, command=lambda: self._move_selected_step(-1)).pack(side=LEFT, padx=2)
        Button(step_toolbar, text="↓", width=2, command=lambda: self._move_selected_step(1)).pack(side=LEFT, padx=2)
        Button(step_toolbar, text="+ Add", width=5, command=self._add_step_popup).pack(side=LEFT, padx=2)
        Button(step_toolbar, text="Trim Moves", width=10, command=self._trim_cursor_moves).pack(side=LEFT, padx=2)
        Button(step_toolbar, text="Delete Step", width=10, command=self._delete_selected_step).pack(side=LEFT, padx=2)

        list_border = TkFrame(self, bg="#3c3c3c", padx=1, pady=1)
        list_border.pack(expand=True, fill=BOTH, padx=14, pady=4)
        list_frame = Frame(list_border)
        list_frame.pack(expand=True, fill=BOTH)
        sb = Canvas(list_frame, width=10, height=1, bg="#262626", highlightthickness=0, bd=0)
        sb.pack(side=RIGHT, fill=Y)

        def _upd_sb(lo, hi):
            sb.delete("all")
            lo, hi = float(lo), float(hi)
            h = max(1, sb.winfo_height())
            y1 = max(2, int(lo * h) + 2)
            y2 = min(h - 2, max(y1 + 18, int(hi * h) - 2))
            sb.create_rectangle(2, y1, 8, y2, fill="#5c5c5c", outline="")

        self.action_list = Listbox(list_frame, selectmode="extended", yscrollcommand=_upd_sb, bg="#1e1e1e", fg="#e0e0e0", selectbackground="#2b5b84", font=("Helvetica Neue", 11), height=4, highlightthickness=0, bd=0)
        self.action_list.bind("<Double-Button-1>", lambda e: self._edit_selected_step())
        self.action_list.pack(side=LEFT, expand=True, fill=BOTH)
        sb.bind("<Configure>", lambda e: _upd_sb(*self.action_list.yview()))
        sb.bind("<B1-Motion>", lambda e: self.action_list.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))
        sb.bind("<Button-1>", lambda e: self.action_list.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))

        hk = self.settings.settings_dict["Hotkeys"]
        fmt = lambda k: "+".join(self._fmt_key(x) for x in k)
        self.hk_lbl = Label(self, text=f"Start Rec: {fmt(hk['Record_Start'])}  |  Stop Rec: {fmt(hk['Record_Stop'])}  |  Play: {fmt(hk['Playback_Start'])}  |  Stop: {fmt(hk['Playback_Stop'])}", font=("Helvetica Neue", 12))
        self.hk_lbl.pack(side="bottom", pady=4)

        from windows.options.playback.speed import Speed
        from windows.options.playback.delay import Delay
        from windows.options.settings.hotkeys import Hotkeys
        from windows.options.settings.settings_popup import SettingsPopup
        from windows.help.about import About
        bar1 = Frame(self)
        bar1.pack(side="bottom", pady=(2, 4))
        for lbl, fn in [("Speed", lambda: Speed(self, self)), ("Loop Delay", lambda: Delay(self, self)), ("Rec Delay", lambda: __import__("windows.options.recording.start_delay", fromlist=["StartDelay"]).StartDelay(self, self)), ("Hotkeys", lambda: Hotkeys(self, self)), ("Settings", lambda: SettingsPopup(self, self))]:
            Button(bar1, text=lbl, width=10, command=fn).pack(side=LEFT, padx=4)

        for cls_name in ("TButton", "Button", "TCheckbutton", "Checkbutton"):
            self.bind_class(cls_name, "<Enter>", lambda e: e.widget.configure(cursor="pointinghand"), add="+")
            self.bind_class(cls_name, "<Leave>", lambda e: e.widget.configure(cursor=""), add="+")

        bar2 = Frame(self)
        bar2.pack(side="bottom", pady=(4, 2))
        for lbl, fn in [("Load", record_management.load_macro), ("Save", record_management.save_macro), ("Save As", record_management.save_macro_as), ("About", lambda: About(self, self, self.version.version, self.version.update))]:
            Button(bar2, text=lbl, width=10, command=fn).pack(side=LEFT, padx=4)

        if self.settings.settings_dict["Others"]["Check_update"]:
            if self.version.new_version != "" and self.version.version != self.version.new_version:
                if time() > self.settings.settings_dict["Others"]["Remind_new_ver_at"]:
                    NewVerAvailable(self, self.version.new_version)

        from windows.others.permissions_popup import PermissionsPopup, check_macos_permissions
        if sys.platform == "darwin" and not self.settings.settings_dict.get("Others", {}).get("Skip_perm_prompt", False):
            im_ok, post_ok = check_macos_permissions()
            if not (im_ok and post_ok):
                self.after(250, lambda: self.show_permissions_popup(startup=True))

        self.protocol("WM_DELETE_WINDOW", self.quit_software)
        try:
            self.createcommand("::tk::mac::Quit", self.quit_software)
        except Exception:
            pass
        self._last_ev_sig = None
        self._refresh_coords()
        self._refresh_dashboard()
        # Tk on macOS plays the system alert sound when a key press reaches the
        # window with no binding; that is what happens to the stop hotkey just as
        # we pull the window forward after recording. Mark keys as handled.
        try:
            self.bind_all("<KeyPress>", lambda event: None, add="+")
            self.bind_all("<KeyRelease>", lambda event: None, add="+")
        except Exception:
            pass
        self.geometry("700x490")
        # Never let the window shrink below the size it opens in.
        self.minsize(700, 490)
        if sys.platform == "darwin":
            self.after(100, self._bring_main_window_forward)
        self.mainloop()

    @staticmethod
    def _menubar_log(message):
        try:
            from datetime import datetime
            log_path = path.join(path.expanduser("~"), "Desktop", "lyrro_menubar.log")
            with open(log_path, "a", encoding="utf-8") as handle:
                handle.write("%s %s\n" % (datetime.now().strftime("%H:%M:%S"), message))
        except Exception:
            pass

    def _bring_main_window_forward(self):
        self._menubar_log("bring forward")
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication, NSApplicationActivationPolicyRegular
                ns_app = NSApplication.sharedApplication()
                if not getattr(self, "_activation_policy_set", False):
                    ns_app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
                    self._activation_policy_set = True
                # Re-activating an already active app on the same run-loop tick
                # as a hotkey release makes macOS play its alert sound ("boop").
                if not ns_app.isActive():
                    ns_app.activateIgnoringOtherApps_(True)
            except Exception:
                pass
        try:
            self.deiconify()
            self.lift()
            if sys.platform == "darwin":
                # Forcing focus on a window that became visible in this same
                # tick is the other half of that alert; let it settle first.
                self.after(140, self._focus_main_window)
            else:
                self.focus_force()
        except Exception:
            pass

    def _focus_main_window(self):
        try:
            if self.winfo_exists() and self.winfo_viewable():
                self.focus_set()
        except Exception:
            pass

    def show_permissions_popup(self, startup=False):
        if self._permissions_popup_open:
            return
        from windows.others.permissions_popup import PermissionsPopup

        self._permissions_popup_open = True
        try:
            PermissionsPopup(self, self, startup=startup)
        finally:
            self._permissions_popup_open = False

    def request_permissions_popup(self, status=None):
        if self._permissions_popup_open or self._permissions_popup_pending:
            return
        self._permissions_popup_pending = True

        def open_popup():
            self._permissions_popup_pending = False
            if status:
                self.status_text.configure(text=status)
            self.show_permissions_popup(startup=False)

        try:
            self.after(0, open_popup)
        except Exception:
            self._permissions_popup_pending = False

    def _toggle_infinite(self, save=True):
        inf = self.inf_var.get()
        self.rep_entry.configure(state="disabled" if inf else "normal")
        if inf:
            self.rep_entry.select_clear()
            self.focus_set()
        if save:
            self.settings.settings_dict["Playback"]["Repeat"]["Infinite"] = inf
            self.settings.save_settings()

    def _apply_inline_repeat(self):
        try:
            val = max(1, int(self.rep_var.get().strip()))
            self.rep_var.set(str(val))
            rep = self.settings.settings_dict["Playback"]["Repeat"]
            rep["Infinite"] = self.inf_var.get()
            rep["Times"] = val
            self.settings.save_settings()
            self.status_text.configure(text=f"Loops set to {'∞' if rep['Infinite'] else val}")
        except ValueError:
            pass

    def _clear_macro(self):
        if self.macro.record or self.macro.playback:
            return
        if self.macro.macro_events.get("events"):
            from tkinter import messagebox
            title = self.text_content.get("global", {}).get("confirm", "Confirm")
            if not messagebox.askyesno(title, "Clear this recording? This cannot be undone.", parent=self):
                return
        if self.macro.macro_events.get("events"):
            from tkinter import messagebox
            title = self.text_content.get("global", {}).get("confirm", "Confirm")
            if not messagebox.askyesno(title, "Clear this recording? This cannot be undone.", parent=self):
                return
        self.macro.macro_events = {"events": []}
        self.macro_recorded = False
        self.macro_saved = True
        self.current_file = None
        self.playBtn.configure(state=DISABLED)
        self.status_text.configure(text="Recording cleared")

    def _trim_cursor_moves(self):
        evs = self.macro.macro_events.get("events", [])
        sel = set(self.action_list.curselection())
        if len(sel) >= 2:
            lo, hi = min(sel), max(sel)
            self.macro.macro_events["events"] = [e for i, e in enumerate(evs) if not (lo <= i <= hi and e.get("type") == "cursorMove")]
        else:
            self.macro.macro_events["events"] = [e for e in evs if e.get("type") != "cursorMove"]
        self.macro_saved = False
        self._last_ev_sig = None

    def _move_selected_step(self, delta):
        sel = self.action_list.curselection()
        if len(sel) != 1:
            return
        idx = sel[0]
        evs = self.macro.macro_events.get("events", [])
        new_idx = idx + delta
        if 0 <= idx < len(evs) and 0 <= new_idx < len(evs):
            evs[idx], evs[new_idx] = evs[new_idx], evs[idx]
            self._pending_select = new_idx
            self.macro_saved = False
            self._last_ev_sig = None

    def _add_step_popup(self):
        from windows.others.step_editor import StepEditor
        StepEditor(self, self)

    def _edit_selected_step(self):
        sel = self.action_list.curselection()
        if len(sel) != 1:
            return
        idx = sel[0]
        evs = self.macro.macro_events.get("events", [])
        if 0 <= idx < len(evs):
            from windows.others.step_editor import StepEditor
            StepEditor(self, self, step_index=idx, existing_step=evs[idx])

    def _delete_selected_step(self):
        sel = self.action_list.curselection()
        if not sel:
            return
        evs = self.macro.macro_events.get("events", [])
        valid_indices = [idx for idx in sel if 0 <= idx < len(evs)]
        if valid_indices:
            for idx in reversed(valid_indices):
                evs.pop(idx)
            self.macro_recorded = bool(evs)
            self._pending_select = min(min(valid_indices), max(0, len(evs) - 1))
            self.macro_saved = False
            self._last_ev_sig = None
            self.playBtn.configure(state=NORMAL if evs else DISABLED, command=self.macro.start_playback)

    def _refresh_coords(self):
        try:
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            text = f"Cursor: X={x} Y={y}"
            if text != getattr(self, "_last_coord_text", None):
                self._last_coord_text = text
                self.coord_lbl.config(text=text)
        except Exception:
            pass
        self.after(66, self._refresh_coords)

    @staticmethod
    def _fmt_key(k):
        return format_key_name(k)

    def _refresh_dashboard(self):
        if getattr(self, "_open_requested", False):
            self._open_requested = False
            try:
                self._bring_main_window_forward()
            except Exception:
                pass
        badge = ((u"● RECORDING...", "#FF5252") if self.macro.record else
                 (u"▶ PLAYING...", "#40C4FF") if self.macro.playback else
                 (u"● READY", "#4CAF50"))
        if badge != getattr(self, "_last_badge", None):
            self._last_badge = badge
            self.status_badge.config(text=badge[0], foreground=badge[1])
        f = path.basename(self.current_file) if self.current_file else ("Unsaved Recording" if self.macro_recorded else "None")
        if f != getattr(self, "_last_file_text", None):
            self._last_file_text = f
            self.file_lbl.config(text=f"Loaded: {f}")
        evs = self.macro.macro_events.get("events", [])
        sig = (len(evs), str(evs[-1]) if evs else "")
        if sig != self._last_ev_sig:
            self._last_ev_sig = sig
            self.steps_lbl.config(text=f"Recorded Actions ({len(evs)} steps):")
            self.action_list.delete(0, END)
            for i, e in enumerate(evs):
                t = e.get("type", "")
                ts = round(e.get("timestamp", 0), 2)
                if t == "cursorMove":
                    txt = f"{i+1}. Move ({int(e.get('x',0))}, {int(e.get('y',0))})  [{ts}s]"
                elif t in ("leftClickEvent", "rightClickEvent", "middleClickEvent"):
                    label = STEP_TYPE_LABELS.get(t, t)
                    txt = f"{i+1}. {label} ({int(e.get('x',0))}, {int(e.get('y',0))}) {'Down' if e.get('pressed') else 'Up'}  [{ts}s]"
                elif t == "scrollEvent":
                    label = STEP_TYPE_LABELS.get(t, t)
                    txt = f"{i+1}. {label} ({int(e.get('dx',0))}, {int(e.get('dy',0))})  [{ts}s]"
                elif t == "keyboardEvent":
                    txt = f"{i+1}. Key {self._fmt_key(e.get('key',''))} {'Down' if e.get('pressed') else 'Up'}  [{ts}s]"
                else:
                    txt = f"{i+1}. {t}  [{ts}s]"
                self.action_list.insert(END, txt)
                if t == "keyboardEvent":
                    kname = self._fmt_key(e.get("key", ""))
                    is_cmd = kname in ("Cmd", "Ctrl", "Option", "Shift", "Fn")
                    self.action_list.itemconfig(i, fg="#FFD54F" if is_cmd else "#81C784")
                elif t == "cursorMove":
                    self.action_list.itemconfig(i, fg="#9e9e9e")
                else:
                    self.action_list.itemconfig(i, fg="#4FC3F7")
            if evs:
                pending = getattr(self, "_pending_select", None)
                if pending is not None and 0 <= pending < len(evs):
                    self.action_list.selection_set(pending)
                    self.action_list.see(pending)
                    self._pending_select = None
                else:
                    self.action_list.see(END)
        try:
            if self.macro.playback:
                if self._playback_started is None:
                    self._playback_started = time()
                    self._menubar_log("playback started")
            else:
                if self._playback_started is not None:
                    self._menubar_log("playback ended")
                self._playback_started = None
            mbs = getattr(self, "menu_bar_status", None)
            if not mbs:
                self._menubar_log("menu_bar_status is None")
            if mbs:
                rec_started = getattr(self.macro, "record_started_at", None)
                recording_now = bool(self.macro.record and rec_started)
                rec = (time() - rec_started) if recording_now else 0.0
                ply = (time() - self._playback_started) if self._playback_started else 0.0
                mbs.update(self.macro.record, getattr(self.macro, "counting_down", False),
                           getattr(self.macro, "countdown_left", 0), self.macro.playback, rec, ply)
        except Exception:
            import traceback
            self._menubar_log("menubar block error:\n" + traceback.format_exc())
        self.after(120, self._refresh_dashboard)


    def _has_open_modal(self):
        if getattr(self, "allow_quit_on_startup_perms", False):
            return False
        if getattr(self, "prevent_record", False):
            return True
        from tkinter import Toplevel
        return any(isinstance(w, Toplevel) and w.winfo_exists() for w in self.winfo_children())

    def quit_software(self, force=False):
        if getattr(self, "_quitting", False):
            return
        if not force and self._has_open_modal():
            try:
                self.status_text.configure(text="Close the open dialog before quitting")
            except Exception:
                pass
            return
        try:
            if getattr(self, "macro", None):
                if self.macro.playback:
                    self.macro.stop_playback(True)
                if self.macro.record or self.macro.counting_down:
                    self.macro.stop_record()
        except Exception:
            pass
        self._finish_quit()

    def _finish_quit(self):
        """Quit through AppKit so macOS does not record an abnormal exit.

        Leaving from inside a Tcl callback (sys.exit, or Tk.destroy) is what
        produced the "quit unexpectedly" dialog. NSApplication.terminate_ runs
        the normal quit sequence and exits with status 0.
        """
        if getattr(self, "_quitting", False):
            return
        self._quitting = True
        self._menubar_log("quit: start")
        try:
            status_bar = getattr(self, "menu_bar_status", None)
            if status_bar is not None:
                status_bar.remove()
            self._menubar_log("quit: status item removed")
        except Exception as exc:
            self._menubar_log("quit: status remove failed %r" % (exc,))
        if sys.platform == "darwin":
            self._menubar_log("quit: terminating")
            try:
                from AppKit import NSApplication
                NSApplication.sharedApplication().terminate_(None)
                self._menubar_log("quit: terminate returned")
            except Exception as exc:
                self._menubar_log("quit: terminate failed %r" % (exc,))
            try:
                import os
                self._menubar_log("quit: exiting")
                os._exit(0)
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass
        sys.exit(0)

    def load_language(self):
        self.lang = self.settings.settings_dict["Language"]
        with open(resource_path(path.join('langs', self.lang + '.json')), encoding='utf-8') as f:
            self.text_content = json.load(f)
        self.text_content = self.text_content["content"]

        if self.lang != "en":
            with open(resource_path(path.join('langs', 'en.json')), encoding='utf-8') as f:
                en = json.load(f)
            deepcopy_dict_missing_entries(self.text_content, en["content"])


    def systemTray(self):
        if sys.platform == "darwin":
            return
        image = Image.open(resource_path(path.join("assets", "logo.ico")))
        menu = (MenuItem("Show", self.deiconify, default=True),)
        self.icon = Icon("Lyrro's Macro Recorder", image, "Lyrro's Macro Recorder", menu)
        self.icon.run()
