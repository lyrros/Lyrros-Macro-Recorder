from tkinter import BooleanVar
from tkinter.ttk import Frame, Label, Button, Checkbutton
from windows.popup import Popup
from windows.options.settings import AfterPlayBack, SelectLanguage
from windows.others.permissions_popup import PermissionsPopup


class SettingsPopup(Popup):
    def __init__(self, parent, main_app):
        super().__init__("Settings", 510, 495, parent)
        self.resizable(False, False)
        self.main_app = main_app
        settings = main_app.settings
        cfg = settings.settings_dict
        menu = main_app.menu

        Label(self, text="Settings", font=("Helvetica Neue", 15, "bold")).pack(pady=(14, 2))
        Label(self, text="Configure recording filters, window behavior, and saving options", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 10))

        body = Frame(self)
        body.pack(fill="both", expand=True, padx=24)

        Label(body, text="Recording Filters", font=("Helvetica Neue", 12, "bold"), foreground="#40C4FF").pack(anchor="w", pady=(2, 4))
        self._add_chk(body, "Record Mouse Movement", menu.mouseMove, lambda: settings.change_settings("Recordings", "Mouse_Move"))
        self._add_chk(body, "Record Mouse Clicks", menu.mouseClick, lambda: settings.change_settings("Recordings", "Mouse_Click"))
        self._add_chk(body, "Record Keyboard Input", menu.keyboardInput, lambda: settings.change_settings("Recordings", "Keyboard"))
        self._add_chk(body, "Show Events on Status Bar", menu.showEventsOnStatusBar, lambda: settings.change_settings("Recordings", "Show_Events_On_Status_Bar"))

        Label(body, text="Behavior & Saving", font=("Helvetica Neue", 12, "bold"), foreground="#40C4FF").pack(anchor="w", pady=(10, 4))
        self._add_chk(body, "Minimize When Playing", menu.minimization_playing, lambda: settings.change_settings("Minimization", "When_Playing"))
        self._add_chk(body, "Minimize When Recording", menu.minimization_record, lambda: settings.change_settings("Minimization", "When_Recording"))
        self._add_chk(body, "Compact JSON Saving", menu.compactJson, lambda: settings.change_settings("Saving", "Compact_json"))
        self._add_chk(body, "Always Import Macro Settings", menu.always_import_macro_settings, lambda: settings.change_settings("Loading", "Always_import_macro_settings"))
        self._add_chk(body, "Check for Updates on Startup", menu.Check_update, lambda: settings.change_settings("Others", "Check_update"))

        sub_row = Frame(self)
        sub_row.pack(pady=(10, 6))
        Button(sub_row, text="Language", width=12, command=lambda: SelectLanguage(self, main_app)).pack(side="left", padx=4)
        Button(sub_row, text="After Playback", width=13, command=lambda: AfterPlayBack(self, main_app)).pack(side="left", padx=4)
        Button(sub_row, text="Permissions", width=12, command=lambda: PermissionsPopup(self, main_app, startup=False)).pack(side="left", padx=4)

        btns = Frame(self)
        btns.pack(side="bottom", pady=(6, 14))
        Button(btns, text="Done", width=12, command=self.destroy).pack()

    def _add_chk(self, parent, text, var, cmd):
        Checkbutton(parent, text=text, variable=var, onvalue=True, offvalue=False, command=cmd).pack(anchor="w", pady=2)
