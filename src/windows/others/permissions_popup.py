import ctypes
import subprocess
import sys
from tkinter import BooleanVar
from tkinter.ttk import Button, Checkbutton, Frame, Label
from windows.popup import Popup

APP_VERSION = "v1.0.7"


def _probe_event_tap():
    try:
        cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cf = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        cg.CGEventTapCreate.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p]
        cg.CGEventTapCreate.restype = ctypes.c_void_p
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)(lambda p, t, e, r: e)
        tap = cg.CGEventTapCreate(1, 0, 1, (1 << 10) | (1 << 12), cb, None)
        if tap:
            cf.CFRelease(tap)
            return True
    except Exception:
        pass
    return False


def _request_ax_prompt():
    try:
        app_svc = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        cf = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p
        cf.CFDictionaryCreate.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
        cf.CFDictionaryCreate.restype = ctypes.c_void_p
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        app_svc.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
        app_svc.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
        key = cf.CFStringCreateWithCString(None, b"AXTrustedCheckOptionPrompt", 0x08000100)
        k_true = ctypes.c_void_p.in_dll(cf, "kCFBooleanFalse")
        k_keys = ctypes.c_void_p.in_dll(cf, "kCFTypeDictionaryKeyCallBacks")
        k_vals = ctypes.c_void_p.in_dll(cf, "kCFTypeDictionaryValueCallBacks")
        opts = cf.CFDictionaryCreate(None, (ctypes.c_void_p * 1)(key), (ctypes.c_void_p * 1)(k_true), 1, ctypes.byref(k_keys), ctypes.byref(k_vals))
        ok = bool(app_svc.AXIsProcessTrustedWithOptions(opts))
        cf.CFRelease(opts)
        cf.CFRelease(key)
        return ok
    except Exception:
        return False


def check_macos_permissions(prompt=False):
    if sys.platform != "darwin":
        return True, True
    ax_ok = im_ok = False
    try:
        app_svc = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        app_svc.AXIsProcessTrusted.restype = ctypes.c_bool
        ax_ok = bool(app_svc.AXIsProcessTrusted()) or (prompt and _request_ax_prompt())
    except Exception:
        pass
    try:
        cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cg.CGPreflightListenEventAccess.restype = ctypes.c_bool
        im_ok = bool(cg.CGPreflightListenEventAccess()) or _probe_event_tap()
        if prompt and not im_ok:
            cg.CGRequestListenEventAccess.restype = ctypes.c_bool
            im_ok = bool(cg.CGRequestListenEventAccess()) or _probe_event_tap()
    except Exception:
        pass
    return ax_ok, im_ok


class PermissionsPopup(Popup):
    def __init__(self, parent, main_app, startup=True):
        title = "macOS Permissions Required" if startup else "macOS Permissions"
        super().__init__(title, 575, 465 if startup else 420, parent)
        self.resizable(False, False)
        self.main_app = main_app
        self._poll_job = None

        Label(self, text=title, font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        sub = "To record and play back mouse & keyboard actions, macOS requires permission for Lyrro's Macro Recorder." if startup else "Check your current macOS permission status or jump straight to System Settings anytime."
        Label(self, text=sub, font=("Helvetica Neue", 11), foreground="#b0b0b0", wraplength=480, justify="center").pack(pady=(0, 14))

        card = Frame(self)
        card.pack(fill="x", padx=28, pady=2)
        card.columnconfigure(0, weight=1)

        r1 = Frame(card)
        r1.grid(row=0, column=0, sticky="w", pady=(4, 0))
        Label(r1, text="1. Accessibility", font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.ax_lbl = Label(r1, text="", font=("Helvetica Neue", 11, "bold"))
        self.ax_lbl.pack(side="left", padx=(10, 0))
        Button(card, text="Open Settings", width=14, command=lambda: self._open_settings("Privacy_Accessibility")).grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(card, text="Lets the app control your cursor, clicks, and keys.", font=("Helvetica Neue", 10), foreground="#9e9e9e", wraplength=375, justify="left").grid(row=1, column=0, sticky="w", pady=(2, 12))

        r2 = Frame(card)
        r2.grid(row=2, column=0, sticky="w", pady=(4, 0))
        Label(r2, text="2. Input Monitoring", font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.im_lbl = Label(r2, text="", font=("Helvetica Neue", 11, "bold"))
        self.im_lbl.pack(side="left", padx=(10, 0))
        Button(card, text="Open Settings", width=14, command=lambda: self._open_settings("Privacy_ListenEvent")).grid(row=2, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(card, text="Lets the app record keystrokes and global hotkeys.", font=("Helvetica Neue", 10), foreground="#9e9e9e", wraplength=375, justify="left").grid(row=3, column=0, sticky="w", pady=(2, 10))

        Label(self, text="Tip: Toggle Lyrro's Macro Recorder ON in System Settings, then press Cmd + Q and reopen to apply.", font=("Helvetica Neue", 10), foreground="#8e8e8e", wraplength=495, justify="center").pack(pady=(6, 6))

        if startup:
            self.skip_var = BooleanVar(value=main_app.settings.settings_dict.get("Others", {}).get("Skip_perm_prompt", False))
            Checkbutton(self, text="Don't show this prompt on startup again", variable=self.skip_var, command=self._save_skip).pack(pady=(2, 6))

        Label(self, text=f"Lyrro's Macro Recorder  \u2022  {APP_VERSION}", font=("Helvetica Neue", 10), foreground="#6e6e6e").pack(side="bottom", pady=(0, 8))
        btns = Frame(self)
        btns.pack(side="bottom", pady=(6, 8))
        Button(btns, text="Re-check Status", width=15, command=lambda: self._refresh(prompt=False)).pack(side="left", padx=6)
        Button(btns, text="Continue" if startup else "Done", width=12, command=self._close).pack(side="left", padx=6)

        self._refresh(prompt=False)
        self._schedule_poll()
        main_app.prevent_record = True
        main_app.allow_quit_on_startup_perms = bool(startup)
        try:
            self.wait_window()
        finally:
            self._cancel_poll()
            main_app.allow_quit_on_startup_perms = False
            main_app.prevent_record = False

    def _open_settings(self, pane):
        if pane == "Privacy_Accessibility":
            _request_ax_prompt()
        self._refresh(prompt=False)
        subprocess.run(["open", f"x-apple.systempreferences:com.apple.preference.security?{pane}"])

    def _schedule_poll(self):
        if self.winfo_exists():
            self._refresh(prompt=False)
            self._poll_job = self.after(1500, self._schedule_poll)

    def _cancel_poll(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
            self._poll_job = None

    def _close(self):
        self._cancel_poll()
        self.destroy()

    def _save_skip(self):
        self.main_app.settings.settings_dict.setdefault("Others", {})["Skip_perm_prompt"] = bool(self.skip_var.get())
        self.main_app.settings.save_settings()

    def _refresh(self, prompt=False):
        ax_ok, im_ok = check_macos_permissions(prompt=prompt)
        self.ax_lbl.config(text="\u25cf Granted" if ax_ok else "\u25cf Missing", foreground="#4CAF50" if ax_ok else "#FF5252")
        self.im_lbl.config(text="\u25cf Granted" if im_ok else "\u25cf Missing", foreground="#4CAF50" if im_ok else "#FF5252")
