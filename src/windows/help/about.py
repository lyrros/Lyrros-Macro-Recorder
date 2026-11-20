from tkinter import Text
from tkinter.ttk import Button, Frame, Label
from webbrowser import open as OpenUrl
from windows.popup import Popup

FORK_VERSION = "v1.0.9 (Beta)"

CHANGELOG_TEXT = (
    'v1.0.9 (Beta)\n'
    '• Added an icon to the Menu Bar (for the normal people who aren’t nerds like me, that means the bar on top where the Apple logo is)\n'
    '• Added a recording timer: This is in the same place that the new icon is, it shows your count in real time!\n'
    '• Playback elapsed time option added: This is in settings, it acts the same way the recording indicator does but instead shows how long the macro has been running, along with whatever hotkeys you have set to start/stop the macro (May be bugged, still testing it)\n'
    '• Clicking the menu bar icon opens a dropdown with two choices. Those being “Open Macro” which brings the macro window to the front instantly, and “Quit Macro” to close it instantly\n'
    '\n'
    'v1.0.8 (Beta)\n'
    '• Updated Perms again: The permission screen now also shows Input Monitoring and the macOS permission used for sending playback events, also added a restart-to-apply button\n'
    '• Added a bring app to front toggle option in settings: LMR will now bring the window to the front no matter what if you toggle this on\n'
    '• Added step editor and improved the readability of some labels: Add/Edit Step has new UI, and action names and recording key names look less nerdy (I just made it more readable)\n'
    '• Added an option to Export Settings: self explanatory (It\'s in Settings)\n'
    '• Hotkey bug fix: Fixed an issue with stale key states, and the key used to set a hotkey isn\'t viewed as a live hotkey anymore\n'
    '• Layout tweaks: Made the UI have less blank space, and a few minor touch ups you prob will never notice >:)\n'
    '• Added full keyboard support: Dunno why it was removed previously, but now LMR should fully pick up your keyboard inputs!\n'
    '• Added a new option for a Recording Start delay (WIP, may be improved)\n'
    '• Overhauled the Step Reordering, Insertion, Editing & Range Trimming: Should now be much easier to read and use, you can also now move steps for the macro!\n'
    '• New Macro File Format: instead of the legacy ".pmr" files leftover from PyMacroRecord, I\'ve switched them over to be ".lmr" instead. Compatibility still stays, you can still open .json\'s and .pmr\'s with this tweak.\n'
    '• Overwrite config change: You will now be prompted whether to delete your macro entirely when you press the "clear" button to avoid any fatfingering.\n'
    '• "After Playback" menu removed completely: After playback didn\'t have much practical use in the macro and really was just a leftover feature. If requested I\'ll repurpose it, but for now it\'s gone\n'
    '• Version specific macOS App ID & Bigger Default Window: Made the default window 700x490 so all Recorded Action buttons fit into the UI. I also gave v1.0.8 its own unique macOS bundle ID (com.lyrros.macrorecorder.v1-0-8) so permissions register cleanly per version\n'
    '\n'
    'v1.0.7 (Beta)\n'
    '• Reworked the janky, unreliable permission request screen when you first launch the app\n'
    '• Added "Lyrro\'s Macro Recorder GitHub" button to the About section (takes you to the repository)\n\n'
    'v1.0.6 (Beta)\n'
    '• Finally Updated Original GitHub link to https://github.com/LOUDO2/PyMacroRecord/releases\n'
    '• Updated The Change log section with complete v1.0.5 and v1.0.6 release notes cuz I keep forgetting\n'
    '• Changed the Dialogue that pops up when you click the record button without saving your recording to "Do you want to save your recording?"\n'
    '• Fixed the cursor not properly changing when hovering over UI buttons\n'
    '• Moved the "Clear" button down to be on the left of "Trim Moves" instead of next to "Apply" \n'
    '• Currently trying to remove the "Services" submenu on the app bar\n'
    '\n'
    'v1.0.5 (Beta)\n'
    "• Updated the upstream of PyMacroRecord's base to v1.4.7 (Bahasa Indonesia translation, Pillow 13.0.0, safer CLI macro file handling)\n"
    '• Very Slightly Changed the UI spacing but not rlly :/ \n'
    '\n'
    'v1.0.4 (Beta)\n'
    '• Experimentally changed the Canvas lists with native Listbox controls for buttery two-finger trackpad scrolling in After Playback and Language (UI will look different after this change until I figure out how to fix it lmao)\n'
    "• Re-added command & modifier key colour-coding in Recorded Actions' logs (Cmd/Ctrl/Option/Shift/Fn in gold, keys in green, clicks in cyan)\n"
    "• Lyrro's Macro Recorder will not longer close via Cmd + Q while any menu, popup, or file dialog is open\n"
    "• Fixed Original GitHub button to link directly to LOUDO56/PyMacroRecord (I lied I'm working on it sorry)\n"
    '\n'
    'v1.0.3 (Beta)\n'
    "• Completely redid After Playback settings' UI with native macOS controls & countdown delay presets (For the non nerds I just made the UI look nicer)\n"
    "• Wired After Playback Sleep, Log Out, Restart, and Shut Down actions to macOS System Events (This is Experimental, I'll prob be removing it in the near future)\n"
    '• Rebuilt Language selector UI with native macOS controls & language codes\n'
    '• Added a visible Close button to Changelog popup, previously you had to close the window from the top\n'
    '\n'
    'v1.0.2 (Beta)\n'
    '• Made bottom-right version badge clickable with hover underline to open About (Experimental)\n'
    '• Added built-in Changelog viewer inside About (WIP)\n'
    '• Fixed the text wrapping and layout sizing in the macOS Permissions popup (when LMR asks for permissions)\n'
    '\n'
    'v1.0.1 (Beta)\n'
    '• Added macOS startup Permissions onboarding & Settings Permissions manager\n'
    '• Added version indicator to main window and Permissions dialog\n'
    '• Packaged as standalone macOS app bundle\n'
    '\n'
    'v1.0.0-beta.1 — Initial macOS Fork\n'
    '• Completely rebuilt ui for PyMacroRecord\n'
    '• Rebuilt UI for macOS dark mode with native-feeling controls\n'
    '• Added live Recorded Actions list with Delete Step & Trim Moves\n'
    '• Mapped macOS keycodes (<63>, <179>) to readable names (Fn)\n'
    '• Added inline Loops counter, Infinite toggle, and custom Speed/Delay presets\n'
    '• Moved Settings, Hotkeys, and About onto the main dashboard'
)


class ChangelogPopup(Popup):
    def __init__(self, parent):
        super().__init__("Changelog — Lyrro's Macro Recorder", 490, 395, parent)
        self.resizable(False, False)
        Label(self, text="Changelog", font=("Helvetica Neue", 15, "bold")).pack(pady=(14, 2))
        Label(self, text=f"Current Version: {FORK_VERSION}", font=("Helvetica Neue", 11), foreground="#40C4FF").pack(pady=(0, 8))

        btns = Frame(self)
        btns.pack(side="bottom", pady=(6, 14))
        Button(btns, text="Close", width=12, command=self.destroy).pack()

        box = Text(self, wrap="word", font=("Helvetica Neue", 11), bg="#242424", fg="#e0e0e0", relief="flat", padx=12, pady=10, highlightthickness=1, highlightbackground="#3c3c3c")
        box.insert("1.0", CHANGELOG_TEXT.strip())
        box.configure(state="disabled")
        box.pack(fill="both", expand=True, padx=22, pady=(0, 6))


class About(Popup):
    def __init__(self, parent, main_app, version, updated):
        super().__init__("About Lyrro's Macro Recorder", 500, 430, parent)
        self.resizable(False, False)
        self.main_app = main_app
        self.main_app.about_window = self

        Label(self, text=f"Lyrro's Macro Recorder  •  {FORK_VERSION}", font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 2))
        updated_display = updated if updated else "Checking..."
        self.version_label = Label(self, text=f"Upstream Base: {version} ({updated_display})", font=("Helvetica Neue", 11), foreground="#40C4FF")
        self.version_label.pack(pady=(0, 10))

        card = Frame(self)
        card.pack(fill="x", padx=26, pady=4)
        Label(card, text="Hey! This is a custom macOS fork of another macro called PyMacroRecord put together by  me, Lyrro/LyrroFame (@lyrro on Discord. Dm for any requests/questions). I made this macro because I find it absolutely ridiculous that little to no macros for macOS are free. You shouldn't need to cough up money for a basic tool like this.", font=("Helvetica Neue", 11, "bold"), wraplength=440, justify="center").pack(pady=(4, 6))
        Label(card, text="Just to be clear, I didn't make the original program, This is a .app, however the original was a barebones Python executable. Full credit goes to LOUDO for creating PyMacroRecord. What I did with it is rebuilt the UI, changed the layout and overall appearance (mostly, still shares the same original window body) and added some more obvious features. The original PyMacroRecord was not built for macOS, so I decided to make this more native on this OS so you don't have to!", font=("Helvetica Neue", 10), foreground="#b0b0b0", wraplength=440, justify="center").pack(pady=(0, 8))
        Label(card, text="License: GPL v3.0", font=("Helvetica Neue", 10), foreground="#8e8e8e").pack(pady=(2, 4))

        btns_wrap = Frame(self)
        btns_wrap.pack(side="bottom", pady=(8, 16))
        top_row = Frame(btns_wrap)
        top_row.pack(side="top", pady=(0, 6))
        Button(top_row, text="Lyrro's Macro Recorder Github", width=23, command=lambda: OpenUrl("https://github.com/lyrros/Lyrros-Macro-Recorder")).pack()
        btns = Frame(btns_wrap)
        btns.pack(side="top")
        Button(btns, text="Changelog", width=11, command=lambda: ChangelogPopup(self)).pack(side="left", padx=4)
        Button(btns, text="Original GitHub", width=12, command=lambda: OpenUrl("https://github.com/LOUDO2/PyMacroRecord/releases")).pack(side="left", padx=4)
        Button(btns, text="Close", width=9, command=self.destroy).pack(side="left", padx=4)

        self.update_idletasks()
        height = max(380, self.winfo_reqheight() + 8)
        width = 500
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        main_app.prevent_record = True
        self.wait_window()
        main_app.prevent_record = False

    def update_status(self, updated_text: str):
        if getattr(self, "version_label", None):
            version = self.main_app.version.version
            self.version_label.configure(text=f"Upstream Base: {version} ({updated_text})")

    def destroy(self):
        try:
            if hasattr(self.main_app, "about_window"):
                self.main_app.about_window = None
        except Exception:
            pass
        return super().destroy()
