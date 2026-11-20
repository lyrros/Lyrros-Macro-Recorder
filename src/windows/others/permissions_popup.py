import ctypes, os
import platform as platform_info
import subprocess
import sys
from tkinter import BooleanVar
from tkinter import messagebox
from tkinter.ttk import Button, Checkbutton, Frame, Label
from windows.popup import Popup

APP_VERSION = "v1.0.9"


def close_system_settings():
    """Ask the System Settings app to quit after access has been granted."""
    try:
        from AppKit import NSRunningApplication

        settings_apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(
            "com.apple.systempreferences"
        )
        if not settings_apps:
            return True
        closed = True
        for app in settings_apps:
            closed = bool(app.terminate()) and closed
        return closed
    except Exception:
        return False


def check_macos_permissions():
    if sys.platform != "darwin":
        return True, True
    im_ok = post_ok = False
    try:
        cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        try:
            listen_preflight = cg.CGPreflightListenEventAccess
            listen_preflight.restype = ctypes.c_bool
            im_ok = bool(listen_preflight())
        except AttributeError:
            # Input Monitoring was not a separate permission on older macOS.
            im_ok = True

        try:
            post_preflight = cg.CGPreflightPostEventAccess
            post_preflight.restype = ctypes.c_bool
            post_ok = bool(post_preflight())
        except AttributeError:
            # Older macOS versions include event posting under Accessibility.
            try:
                import ApplicationServices

                post_ok = bool(ApplicationServices.AXIsProcessTrusted())
            except Exception:
                post_ok = False
    except Exception:
        pass
    return im_ok, post_ok


class PermissionsPopup(Popup):
    def __init__(self, parent, main_app, startup=True):
        title = "macOS Permissions Required" if startup else "macOS Permissions"
        super().__init__(title, 635, 488 if startup else 438, parent)
        self.resizable(False, False)
        self.main_app = main_app
        self._poll_job = None
        self._rechecked = False
        self._settings_opened_by_us = False
        self._settings_closed_after_grant = False
        self._permissions_missing_when_settings_opened = False
        self._needs_restart = bool(
            getattr(main_app, "macos_im_permission_missing_at_launch", False)
            or getattr(main_app, "macos_post_permission_missing_at_launch", False)
        )

        Label(self, text=title, font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 4))
        sub = "To record and play back mouse & keyboard actions, macOS requires two permissions for Lyrro's Macro Recorder." if startup else "Check the macOS permissions needed for recording and playback."
        Label(self, text=sub, font=("Helvetica Neue", 11), foreground="#b0b0b0", wraplength=540, justify="center").pack(pady=(0, 14))

        card = Frame(self)
        card.pack(fill="x", padx=28, pady=2)
        card.columnconfigure(0, weight=1)

        r1 = Frame(card)
        r1.grid(row=0, column=0, sticky="w", pady=(4, 0))
        Label(r1, text="1. Input Monitoring", font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.im_lbl = Label(r1, text="", font=("Helvetica Neue", 11, "bold"))
        self.im_lbl.pack(side="left", padx=(10, 0))
        Button(card, text="Open Settings", width=16, command=lambda: self._open_settings("Privacy_ListenEvent")).grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(card, text="Lets the app record keystrokes, mouse actions, and global hotkeys. If it isn't listed here, click Show App in Finder and drag the app into the list.", font=("Helvetica Neue", 10), foreground="#9e9e9e", wraplength=375, justify="left").grid(row=1, column=0, sticky="w", pady=(2, 12))

        r2 = Frame(card)
        r2.grid(row=2, column=0, sticky="w", pady=(4, 0))
        Label(r2, text=self._post_permission_name(), font=("Helvetica Neue", 12, "bold")).pack(side="left")
        self.post_lbl = Label(r2, text="", font=("Helvetica Neue", 11, "bold"))
        self.post_lbl.pack(side="left", padx=(10, 0))
        Button(card, text="Open Settings", width=16, command=lambda: self._open_settings("Privacy_PostEvent")).grid(row=2, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=4)
        Label(card, text=self._post_permission_help(), font=("Helvetica Neue", 10), foreground="#9e9e9e", wraplength=375, justify="left").grid(row=3, column=0, sticky="w", pady=(2, 10))

        Label(self, text="After both permissions show Granted, System Settings closes. Click Restart to Apply if the permission changed after launch.", font=("Helvetica Neue", 10), foreground="#8e8e8e", wraplength=540, justify="center").pack(pady=(6, 6))

        if startup:
            self.skip_var = BooleanVar(value=main_app.settings.settings_dict.get("Others", {}).get("Skip_perm_prompt", False))
            Checkbutton(self, text="Don't show this prompt on startup again", variable=self.skip_var, command=self._save_skip).pack(pady=(2, 6))

        Label(self, text=f"Lyrro's Macro Recorder  \u2022  {APP_VERSION}", font=("Helvetica Neue", 10), foreground="#6e6e6e").pack(side="bottom", pady=(0, 8))
        btns = Frame(self)
        btns.pack(side="bottom", pady=(6, 8))
        Button(btns, text="Re-check Status", width=15, command=self._recheck).pack(side="left", padx=6)
        Button(btns, text="Show App in Finder", width=18, command=self._show_app_in_finder).pack(side="left", padx=6)
        self.restart_btn = Button(btns, text="Restart to Apply", width=16, command=self._restart_app)
        self.restart_btn.pack(side="left", padx=6)
        Button(btns, text="Continue" if startup else "Done", width=12, command=self._close).pack(side="left", padx=6)

        self._refresh()
        self._schedule_poll()
        main_app.prevent_record = True
        main_app.allow_quit_on_startup_perms = True
        try:
            self.wait_window()
        finally:
            self._cancel_poll()
            main_app.allow_quit_on_startup_perms = False
            main_app.prevent_record = False

    @staticmethod
    def _post_permission_name():
        try:
            version = tuple(int(part) for part in platform_info.mac_ver()[0].split(".")[:2])
        except (TypeError, ValueError):
            version = ()
        if version and version >= (27, 3):
            return "2. System & App Protection Override"
        if version and version >= (27, 0):
            return "2. Device Control and Data Access"
        return "2. Accessibility"

    @classmethod
    def _post_permission_help(cls):
        name = cls._post_permission_name().split(". ", 1)[-1]
        return f"Allows playback to send keyboard and mouse actions. Enable Lyrro's Macro Recorder in Privacy & Security > {name}."

    def _show_app_in_finder(self):
        try:
            if getattr(sys, "frozen", False):
                executable = os.path.abspath(sys.executable)
                marker = f"{os.sep}Contents{os.sep}MacOS{os.sep}"
                if marker in executable:
                    bundle = executable.split(marker, 1)[0]
                else:
                    bundle = os.path.dirname(executable)
                subprocess.run(["open", "-R", bundle], check=True, timeout=10)
            else:
                subprocess.run(
                    ["open", os.path.dirname(os.path.abspath(__file__))],
                    check=True,
                    timeout=10,
                )
        except Exception as exc:
            messagebox.showerror("Could not open Finder", str(exc), parent=self)

    def _open_settings(self, pane):
        if sys.platform != "darwin":
            messagebox.showinfo("macOS only", "These permissions are only available on macOS.", parent=self)
            return
        try:
            im_ok, post_ok = check_macos_permissions()
            # CGRequestPostEventAccess() raises the macOS alert offering
            # "Open System Settings" / "Deny". It is intentionally not
            # called: this window opens the pane directly instead.
            self._permissions_missing_when_settings_opened = not (im_ok and post_ok)
            self._settings_closed_after_grant = False

            # Match v1.0.7's Privacy & Security deep-link format. The newer
            # PrivacySecurity.extension URL opens only the overview on this macOS.
            # macOS labels this permission "Device Control and Data Access";
            # its settings anchor remains Privacy_Accessibility.
            if pane == "Privacy_PostEvent":
                pane = "Privacy_Accessibility"
            try:
                mac_major = int(platform_info.mac_ver()[0].split(".")[0])
            except (TypeError, ValueError, IndexError):
                mac_major = 0
            settings_pane = (
                "com.apple.settings.PrivacySecurity.extension"
                if mac_major >= 13 else "com.apple.preference.security"
            )
            settings_url = f"x-apple.systempreferences:{settings_pane}?{pane}"
            # Try the relevant pane, then activate Settings itself as a fallback.
            # The pane URL is undocumented on macOS and may be ignored by newer releases.
            pane_opened = False
            try:
                subprocess.run(
                    ["open", settings_url],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
                pane_opened = True
            except (OSError, subprocess.SubprocessError):
                pass
            if not pane_opened:
                subprocess.run(
                    ["open", "-b", "com.apple.systempreferences"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
            self._settings_opened_by_us = True
            self.after(1000, self._refresh)
        except Exception as exc:
            messagebox.showerror("Could not open System Settings", str(exc), parent=self)

    def _schedule_poll(self):
        if self.winfo_exists():
            self._refresh()
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

    def _restart_app(self):
        try:
            if getattr(sys, "frozen", False):
                executable = os.path.abspath(sys.executable)
                marker = f"{os.sep}Contents{os.sep}MacOS{os.sep}"
                if marker not in executable:
                    raise RuntimeError("Could not locate the app bundle to restart.")
                app_bundle = executable.split(marker, 1)[0]
                subprocess.run(
                    ["open", "-n", app_bundle, "--args", "--permissions-restart"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                )
            else:
                subprocess.Popen(
                    [sys.executable, os.path.abspath(sys.argv[0]), *sys.argv[1:]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror("Restart failed", str(exc), parent=self)
            return
        self._close()
        self.main_app.quit_software(force=True)

    def _save_skip(self):
        self.main_app.settings.settings_dict.setdefault("Others", {})["Skip_perm_prompt"] = bool(self.skip_var.get())
        self.main_app.settings.save_settings()

    def _refresh(self):
        im_ok, post_ok = check_macos_permissions()
        # macOS caches the input-monitoring and post-event verdict for the
        # life of the process, so a grant made while this window is open
        # still reads as missing here until the app is relaunched.
        stale = self._settings_opened_by_us or self._rechecked

        def _state(ok):
            if ok:
                return "\u25cf Granted", "#4CAF50"
            if stale:
                return "\u25cf Restart required", "#FFB74D"
            return "\u25cf Missing", "#FF5252"

        im_text, im_colour = _state(im_ok)
        post_text, post_colour = _state(post_ok)
        self.im_lbl.config(text=im_text, foreground=im_colour)
        self.post_lbl.config(text=post_text, foreground=post_colour)
        all_granted = im_ok and post_ok
        self._needs_restart = self._needs_restart or not all_granted
        self.restart_btn.config(
            state="normal" if self._needs_restart and (all_granted or stale) else "disabled"
        )
        if (
            all_granted
            and self._settings_opened_by_us
            and self._permissions_missing_when_settings_opened
            and not self._settings_closed_after_grant
        ):
            self._settings_closed_after_grant = close_system_settings()

    def _recheck(self):
        self._rechecked = True
        self._refresh()
