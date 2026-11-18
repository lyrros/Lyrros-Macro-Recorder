import ctypes
import subprocess
import sys
from tkinter import BooleanVar
from tkinter.ttk import Button, Checkbutton, Frame, Label
from windows.popup import Popup

APP_VERSION = "v1.0.5"


def check_macos_permissions():
    if sys.platform != "darwin":
        return True, True
    ax_ok = False
    im_ok = False
    try:
        app_svc = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        app_svc.AXIsProcessTrusted.restype = ctypes.c_bool
        ax_ok = bool(app_svc.AXIsProcessTrusted())
    except Exception:
        pass
    try:
        cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cg.CGPreflightListenEventAccess.restype = ctypes.c_bool
        im_ok = bool(cg.CGPreflightListenEventAccess())
    except Exception:
        pass
    return ax_ok, im_ok


class PermissionsPopup(Popup):
    def __init__(self, parent, main_app, startup=True):
        title = "macOS Permissions Required" if startup else "macOS Permissions"
        height = 465 if startup else 420
        super().__init__(title, 575, height, parent)
        self.resizable(False, False)
        self.main_app = main_app

        Label(self, text=title, font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        sub_txt = (
            "To record and play back mouse & keyboard actions, macOS requires permission for Lyrro's Macro Recorder."
            if startup
            else "Check your current macOS permission status or jump straight to System Settings anytime."
        )
        Label(
            self,
            text=sub_txt,
            font=("Helvetica Neue", 11),
            foreground="#b0b0b0",
            wraplength=480,
            justify="center",
        ).pack(pady=(0, 14))

        card = Frame(self)
        card.pack(fill="x", padx=28, pady=2)
        card.columnconfigure(0, weight=1)

        r1_top = Frame(card)
        r1_top.grid(row=0, column=0, sticky="w", pady=(4, 0))
        Label(r1_top, text="1. Accessibility", font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.ax_lbl = Label(r1_top, text="", font=("Helvetica Neue", 11, "bold"))
        self.ax_lbl.pack(side="left", padx=(10, 0))
        Button(
            card,
            text="Open Settings",
            width=14,
            command=lambda: subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"]),
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(
            card,
            text="Lets the app control your cursor, clicks, and keys.",
            font=("Helvetica Neue", 10),
            foreground="#9e9e9e",
            wraplength=375,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        r2_top = Frame(card)
        r2_top.grid(row=2, column=0, sticky="w", pady=(4, 0))
        Label(r2_top, text="2. Input Monitoring", font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.im_lbl = Label(r2_top, text="", font=("Helvetica Neue", 11, "bold"))
        self.im_lbl.pack(side="left", padx=(10, 0))
        Button(
            card,
            text="Open Settings",
            width=14,
            command=lambda: subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"]),
        ).grid(row=2, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(
            card,
            text="Lets the app record keystrokes and global hotkeys.",
            font=("Helvetica Neue", 10),
            foreground="#9e9e9e",
            wraplength=375,
            justify="left",
        ).grid(row=3, column=0, sticky="w", pady=(2, 10))

        Label(
            self,
            text="Tip: After toggling permissions ON in System Settings, restart the app for macOS to apply them.",
            font=("Helvetica Neue", 10),
            foreground="#8e8e8e",
            wraplength=480,
            justify="center",
        ).pack(pady=(6, 6))

        if startup:
            self.skip_var = BooleanVar(value=main_app.settings.settings_dict.get("Others", {}).get("Skip_perm_prompt", False))
            Checkbutton(self, text="Don't show this prompt on startup again", variable=self.skip_var, command=self._save_skip).pack(pady=(2, 6))

        Label(self, text=f"Lyrro's Macro Recorder  •  {APP_VERSION}", font=("Helvetica Neue", 10), foreground="#6e6e6e").pack(side="bottom", pady=(0, 8))

        btns = Frame(self)
        btns.pack(side="bottom", pady=(6, 8))
        Button(btns, text="Re-check Status", width=15, command=self._refresh).pack(side="left", padx=6)
        Button(btns, text="Continue" if startup else "Done", width=12, command=self.destroy).pack(side="left", padx=6)

        self._refresh()
        main_app.prevent_record = True
        self.wait_window()
        main_app.prevent_record = False

    def _save_skip(self):
        self.main_app.settings.settings_dict.setdefault("Others", {})["Skip_perm_prompt"] = bool(self.skip_var.get())
        self.main_app.settings.save_settings()

    def _refresh(self):
        ax_ok, im_ok = check_macos_permissions()
        self.ax_lbl.config(text="● Granted" if ax_ok else "● Missing", foreground="#4CAF50" if ax_ok else "#FF5252")
        self.im_lbl.config(text="● Granted" if im_ok else "● Missing", foreground="#4CAF50" if im_ok else "#FF5252")
