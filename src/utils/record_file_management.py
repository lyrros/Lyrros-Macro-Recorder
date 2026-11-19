from json import dumps, load
from os.path import basename, dirname, splitext
from tkinter import DISABLED, NORMAL, filedialog, messagebox

from utils import UserSettings
from utils.warning_pop_up_save import confirm_save


class RecordFileManagement:
    """Manage save and load record from main app"""

    def __init__(self, main_app, menu_bar):
        self.main_app = main_app
        self.menu_bar = menu_bar
        self.config_text = self.menu_bar.text_config

    def save_macro_as(self, event=None):
        if not self.main_app.macro_recorded or self.main_app.macro.playback:
            return
        initialdir = None
        initialfile = None
        if self.main_app.current_file:
            initialdir = dirname(self.main_app.current_file) or None
            current_name = basename(self.main_app.current_file)
            stem, extension = splitext(current_name)
            initialfile = f"{stem}.lmr" if extension.lower() == ".pmr" else current_name

        self.main_app.prevent_record = True
        try:
            selected_file = filedialog.asksaveasfilename(
                filetypes=[("Lyrro's Macro Files", "*.lmr"), ("Json Files", "*.json")],
                defaultextension=".lmr",
                initialdir=initialdir,
                initialfile=initialfile,
            )
            if not selected_file:
                return

            stem, extension = splitext(selected_file)
            if extension.lower() == ".json":
                self.main_app.current_file = selected_file
            elif extension.lower() == ".lmr":
                self.main_app.current_file = selected_file
            else:
                # PMR remains a supported input format, but every save now
                # writes the current LMR format.
                self.main_app.current_file = f"{stem}.lmr"
            self.save_macro()
            self.main_app.macro_saved = True
        finally:
            self.main_app.prevent_record = False

    def save_macro(self, event=None):
        if not self.main_app.macro_recorded or self.main_app.macro.playback:
            return
        if self.main_app.current_file is not None:
            if splitext(self.main_app.current_file)[1].lower() == ".pmr":
                # Migrate a legacy macro on Save without overwriting the old file.
                return self.save_macro_as()
            with open(self.main_app.current_file, "w") as current_file:
                compactJson = UserSettings(self.main_app).settings_dict["Saving"]["Compact_json"]
                userSettings = self.main_app.settings.settings_dict
                macroSettings = {"settings": {
                    "Playback": userSettings["Playback"],
                    "Minimization": userSettings["Minimization"]
                }}
                macroData = {
                    **macroSettings,
                    **self.main_app.macro.macro_events
                }
                if compactJson:
                    json_macroEvents = dumps(macroData, separators=(',', ':'))
                else:
                    json_macroEvents = dumps(macroData, indent=4)
                current_file.write(json_macroEvents)
        else:
            self.save_macro_as()

    def load_macro(self, event=None):
        if self.main_app.macro.playback:
            return
        self.main_app.prevent_record = True
        if not self.main_app.macro_saved and self.main_app.macro_recorded:
            wantToSave = confirm_save(self.main_app)
            if wantToSave:
                self.save_macro()
            elif wantToSave is None:
                self.main_app.prevent_record = False
                return
        macroFile = filedialog.askopenfilename(
            filetypes=[("Lyrro's Macro Files", "*.lmr"), ("Legacy Macro Files", "*.pmr"), ("Json Files", "*.json")],
            defaultextension=".lmr",
        )
        if macroFile:
            self.main_app.playBtn.configure(
                state=NORMAL, command=self.main_app.macro.start_playback
            )
            self.menu_bar.file_menu.entryconfig(
                self.config_text["file_menu"]["save_text"], state=NORMAL, command=self.save_macro
            )
            self.menu_bar.file_menu.entryconfig(
                self.config_text["file_menu"]["save_as_text"], state=NORMAL, command=self.save_macro_as
            )
            self.menu_bar.file_menu.entryconfig(
                self.config_text["file_menu"]["new_text"], state=NORMAL, command=self.new_macro
            )
            with open(macroFile, "r") as macroContent:
                self.main_app.macro.import_record(load(macroContent))
            self.main_app.macro_recorded = True
            self.main_app.macro_saved = True
            self.main_app.current_file = macroFile
            if "settings" in self.main_app.macro.macro_events:
                if not self.main_app.settings.settings_dict["Loading"]["Always_import_macro_settings"]:
                    if messagebox.askyesno("Lyrro's Macro Recorder", self.config_text["global"]["load_macro_settings"]):
                        macro_settings = self.main_app.macro.macro_events["settings"]
                        self.main_app.settings.settings_dict["Playback"] = macro_settings["Playback"]
                        self.main_app.settings.settings_dict["Minimization"] = macro_settings["Minimization"]
        self.main_app.prevent_record = False


    def new_macro(self, event=None):
        if not self.main_app.macro_recorded or self.main_app.macro.playback:
            return
        if not self.main_app.macro_saved and self.main_app.macro_recorded:
            wantToSave = confirm_save(self.main_app)
            if wantToSave:
                self.save_macro()
            elif wantToSave is None:
                return
        self.main_app.playBtn.configure(state=NORMAL)
        self.menu_bar.file_menu.entryconfig(self.config_text["file_menu"]["save_text"], state=DISABLED)
        self.menu_bar.file_menu.entryconfig(self.config_text["file_menu"]["save_as_text"], state=DISABLED)
        self.menu_bar.file_menu.entryconfig(self.config_text["file_menu"]["new_text"], state=DISABLED)
        self.main_app.playBtn.configure(state=DISABLED)
        self.main_app.current_file = None
        self.main_app.macro_saved = False
        self.main_app.macro_recorded = False
