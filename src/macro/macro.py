from utils.key_names import FN_KEY_CODES, format_key_name as _fmt_key

from datetime import datetime
from sys import platform
from threading import Event, Thread
from time import time
from tkinter import DISABLED, NORMAL, messagebox

from pynput import keyboard, mouse
from pynput.keyboard import Key  # FUTURE SELF: DON'T REMOVE THIS!!
from pynput.mouse import Button

from utils.get_key_pressed import getKeyPressed, normalize_key, resolve_key_for_playback
from utils.keys import vk_nb
from utils.macos_keyboard_compat import prepare_pynput_keyboard_listener
from utils.record_file_management import RecordFileManagement
from utils.show_toast import show_notification_minim
from utils.warning_pop_up_save import confirm_save


class Macro:
    """Init a new Macro"""

    def __init__(self, main_app):
        self.showEventsOnStatusBar = None
        prepare_pynput_keyboard_listener()
        self.mouseControl = mouse.Controller()
        self.keyboardControl = keyboard.Controller()
        self.record = False
        self.counting_down = False
        self.playback = False
        self._playback_cancel = Event()
        self.macro_events = {}
        self.main_app = main_app
        self.user_settings = self.main_app.settings
        self.main_menu = self.main_app.menu
        self.macro_file_management = RecordFileManagement(self.main_app, self.main_menu)

        self.mouseBeingListened = None
        self.keyboardBeingListened = None
        self.keyboard_listener = None
        self.mouse_listener = None
        self.time = time()
        self.record_started_at = None
        self.event_delta_time=0

        self.keyboard_listener = keyboard.Listener(
                on_press=self.__on_press, on_release=self.__on_release
            )
        # Same reason as the hotkey listener: no global event tap before
        # Input Monitoring is granted, or macOS raises its own alert.
        if self._keyboard_listener_allowed():
            self.keyboard_listener.start()

    @staticmethod
    def _keyboard_listener_allowed():
        try:
            from windows.others.permissions_popup import check_macos_permissions
            im_ok, _post = check_macos_permissions()
            return bool(im_ok)
        except Exception:
            return True

    def start_record(self, by_hotkey=False):
        if self.main_app.prevent_record:
            return
        if not self._macos_permissions_allow(recording=True):
            return
        if not by_hotkey:
            if not self.main_app.macro_saved and self.main_app.macro_recorded:
                wantToSave = confirm_save(self.main_app)
                if wantToSave:
                    self.macro_file_management.save_macro()
                elif wantToSave is None:
                    return
        delay_sec = int(self.user_settings.settings_dict.get("Recordings", {}).get("Start_Delay", 0) or 0)
        if delay_sec >= 1 and not self.counting_down:
            self.counting_down = True
            self.main_app.recordBtn.configure(image=self.main_app.stopImg, command=self.stop_record)
            self.main_app.playBtn.configure(state=DISABLED)
            self._run_countdown(delay_sec, by_hotkey)
            return
        self.macro_events = {"events": []}
        self.record = True
        self.time = time()
        # self.time is advanced by every recorded event, so the elapsed-time
        # display needs its own start stamp.
        self.record_started_at = self.time
        self.event_delta_time=0
        userSettings = self.user_settings.settings_dict
        self.showEventsOnStatusBar = userSettings["Recordings"]["Show_Events_On_Status_Bar"]
        if (
            userSettings["Recordings"]["Mouse_Move"]
            and userSettings["Recordings"]["Mouse_Click"]
        ):
            self.mouse_listener = mouse.Listener(
                on_move=self.__on_move,
                on_click=self.__on_click,
                on_scroll=self.__on_scroll,
            )
            self.mouse_listener.start()
            self.mouseBeingListened = True
        elif userSettings["Recordings"]["Mouse_Move"]:
            self.mouse_listener = mouse.Listener(
                on_move=self.__on_move, on_scroll=self.__on_scroll
            )
            self.mouse_listener.start()
            self.mouseBeingListened = True
        elif userSettings["Recordings"]["Mouse_Click"]:
            self.mouse_listener = mouse.Listener(
                on_click=self.__on_click, on_scroll=self.__on_scroll
            )
            self.mouse_listener.start()
            self.mouseBeingListened = True
        if userSettings["Recordings"]["Keyboard"]:
            self.keyboardBeingListened = True
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["load_text"], state=DISABLED)
        self.main_app.recordBtn.configure(
            image=self.main_app.stopImg, command=self.stop_record
        )
        self.main_app.playBtn.configure(state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_as_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["new_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["load_text"], state=DISABLED)
        if userSettings["Minimization"]["When_Recording"]:
            self.main_app.withdraw()
            Thread(target=lambda: show_notification_minim(self.main_app)).start()
        print("record started")

    def _run_countdown(self, remaining, by_hotkey=False):
        if not self.counting_down:
            return
        self.countdown_left = remaining
        if remaining <= 0:
            self.counting_down = False
            self.start_record(by_hotkey=True)
            return
        self.main_app.status_text.configure(text=f"Recording starts in {remaining}s... (Press Stop to cancel)")
        self.main_app.after(1000, lambda: self._run_countdown(remaining - 1, by_hotkey))

    def stop_record(self):
        if self.counting_down:
            self.counting_down = False
            self.main_app.recordBtn.configure(image=self.main_app.recordImg, command=self.start_record)
            self.main_app.playBtn.configure(state=NORMAL if self.main_app.macro_recorded else DISABLED, command=self.start_playback)
            self.main_app.status_text.configure(text="Recording countdown canceled")
            return
        if not self.record:
            return
        userSettings = self.user_settings.settings_dict
        self.record = False
        self.counting_down = False
        self.record_started_at = None
        if self.mouseBeingListened:
            self.mouse_listener.stop()
            self.mouseBeingListened = False
        if self.keyboardBeingListened:
            self.keyboardBeingListened = False
        self.main_app.recordBtn.configure(
            image=self.main_app.recordImg, command=self.start_record
        )
        self.main_app.playBtn.configure(state=NORMAL, command=self.start_playback)
        self.main_menu.file_menu.entryconfig(
            self.main_app.text_content["file_menu"]["save_text"], state=NORMAL, command=self.macro_file_management.save_macro
        )
        self.main_menu.file_menu.entryconfig(
            self.main_app.text_content["file_menu"]["save_as_text"], state=NORMAL, command=self.macro_file_management.save_macro_as
        )
        self.main_menu.file_menu.entryconfig(
            self.main_app.text_content["file_menu"]["new_text"], state=NORMAL, command=self.macro_file_management.new_macro
        )
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["load_text"], state=NORMAL)

        self.main_app.macro_recorded = True
        self.main_app.macro_saved = False

        if userSettings["Minimization"].get("When_Recording", False):
            self.main_app.deiconify()
        if userSettings["Minimization"].get("Bring_to_Front_After_Recording", True):
            try:
                self.main_app.after(100, self.main_app._bring_main_window_forward)
            except Exception:
                pass

        print("record stopped")

    def start_playback(self):
        if self.playback:
            return
        if not self._macos_permissions_allow(recording=False):
            return
        events = self.macro_events.get("events", [])
        if not events:
            return
        if platform.lower() == "darwin" and self._contains_cmd_q(events):
            warning = (
                "This macro contains Command+Q, which quits the frontmost macOS app. "
                "Remove that keyboard shortcut from the action list before playing it."
            )
            try:
                self.main_app.after(0, lambda: messagebox.showwarning("Playback blocked", warning))
            except Exception:
                pass
            return

        self._playback_cancel.clear()
        userSettings = self.user_settings.settings_dict
        self.playback = True
        self.main_app.playBtn.configure(
            image=self.main_app.stopImg, command=lambda: self.stop_playback(True)
        )
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_as_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["new_text"], state=DISABLED)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["load_text"], state=DISABLED)
        self.main_app.recordBtn.configure(state=DISABLED)
        if userSettings["Minimization"]["When_Playing"]:
            self.main_app.withdraw()
            Thread(target=lambda: show_notification_minim(self.main_app)).start()
        if userSettings["Playback"]["Repeat"]["Interval"] > 0:
            Thread(target=self.__play_interval).start()
        elif userSettings["Playback"]["Repeat"]["For"] > 0:
            Thread(target=self.__play_for).start()
        elif userSettings["Playback"]["Repeat"]["For"] > 0 and userSettings["Playback"]["Repeat"]["Interval"] > 0:
            Thread(target=self.__play_interval).start()
        else:
            Thread(target=self.__play_events).start()
        print("playback started")

    def _macos_permissions_allow(self, recording):
        if platform.lower() != "darwin":
            return True

        from windows.others.permissions_popup import check_macos_permissions

        im_ok, post_ok = check_macos_permissions()
        im_needs_restart = recording and getattr(
            self.main_app, "macos_im_permission_missing_at_launch", False
        )
        post_needs_restart = not recording and getattr(
            self.main_app, "macos_post_permission_missing_at_launch", False
        )
        if recording:
            missing = not im_ok
            restart_needed = im_needs_restart
        else:
            missing = not post_ok
            restart_needed = post_needs_restart
        if not missing and not restart_needed:
            return True

        if recording and not im_ok:
            status = "Grant Input Monitoring access before recording."
        elif not recording and not post_ok:
            status = "Grant Event Control access before playback."
        else:
            action = "recording" if recording else "playback"
            status = f"Permissions are granted. Click Restart to Apply before {action}."

        try:
            self.main_app.request_permissions_popup(status)
        except Exception:
            pass
        return False

    @staticmethod
    def _contains_cmd_q(events):
        pressed_keys = set()
        for event in events:
            if event.get("type") != "keyboardEvent":
                continue
            key = str(event.get("key", "")).strip().strip("'\"").casefold()
            if key in {"key.cmd", "key.cmd_l", "key.cmd_r", "cmd", "command"}:
                key = "cmd"
            is_pressed = bool(event.get("pressed"))
            if is_pressed and key == "q" and "cmd" in pressed_keys:
                return True
            if is_pressed:
                pressed_keys.add(key)
            else:
                pressed_keys.discard(key)
        return False

    def __play_interval(self):
        userSettings = self.user_settings.settings_dict
        if userSettings["Playback"]["Repeat"]["For"] > 0:
            self.__play_for()
        else:
            self.__play_events()
        timer = time()
        while self.playback:
            if self._playback_cancel.wait(1):
                return
            if time() - timer >= userSettings["Playback"]["Repeat"]["Interval"]:
                if userSettings["Playback"]["Repeat"]["For"] > 0:
                    self.__play_for()
                else:
                    self.__play_events()
                timer = time()


    def __play_for(self):
        userSettings = self.user_settings.settings_dict
        debut = time()
        while self.playback and (time() - debut) < userSettings["Playback"]["Repeat"]["For"]:
            self.__play_events()
        if self.playback and userSettings["Playback"]["Repeat"]["Interval"] == 0:
            self.stop_playback()

    def __play_events(self):
        global keyToPress
        userSettings = self.user_settings.settings_dict
        click_func = {
            "leftClickEvent": Button.left,
            "rightClickEvent": Button.right,
            "middleClickEvent": Button.middle,
        }
        keyToUnpress = []

        is_infinite = userSettings["Playback"]["Repeat"].get("Infinite", False)

        if userSettings["Playback"]["Repeat"]["For"] > 0:
            repeat_times = 1
        elif is_infinite:
            repeat_times = float('inf')
        else:
            repeat_times = userSettings["Playback"]["Repeat"]["Times"]

        if userSettings["Playback"]["Repeat"]["Scheduled"] > 0:
            now = datetime.now()
            seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            secondsToWait = userSettings["Playback"]["Repeat"]["Scheduled"] - seconds_since_midnight
            if secondsToWait < 0:
                secondsToWait = 86400 + secondsToWait  # 86400 + -secondsToWait. Meaning it will happen tomorrow
            if self._playback_cancel.wait(secondsToWait):
                return

        repeat_count = 0
        now = time()

        while self.playback and (is_infinite or repeat_count < repeat_times):
            for events in range(len(self.macro_events["events"])):
                if not self.playback:
                    self.unPressEverything(keyToUnpress)
                    return
                elapsed_time = int(time() - now)
                self.main_app.status_text.configure(
                    text=f"Repeat: {repeat_count + 1}/{repeat_times}, Time elapsed: {elapsed_time}s")

                timeSleep = (
                        self.macro_events["events"][events]["timestamp"]
                        * (1 / userSettings["Playback"]["Speed"])
                )
                if timeSleep < 0:
                    timeSleep = abs(timeSleep)
                if self._playback_cancel.wait(timeSleep) or not self.playback:
                    self.unPressEverything(keyToUnpress)
                    return
                event_type = self.macro_events["events"][events]["type"]

                if event_type == "cursorMove":  # Cursor Move
                    self.mouseControl.position = (
                        self.macro_events["events"][events]["x"],
                        self.macro_events["events"][events]["y"],
                    )

                elif event_type in click_func:  # Mouse Click
                    self.mouseControl.position = (
                        self.macro_events["events"][events]["x"],
                        self.macro_events["events"][events]["y"],
                    )
                    if self.macro_events["events"][events]["pressed"]:
                        self.mouseControl.press(click_func[event_type])
                    else:
                        self.mouseControl.release(click_func[event_type])

                elif event_type == "scrollEvent":
                    self.mouseControl.scroll(
                        self.macro_events["events"][events]["dx"],
                        self.macro_events["events"][events]["dy"],
                    )

                elif event_type == "keyboardEvent":  # Keyboard Press,Release
                    if self.macro_events["events"][events]["key"] is not None:
                        try:
                            keyToPress = resolve_key_for_playback(self.macro_events["events"][events]["key"])
                            if self.playback:
                                if keyToPress is not None:
                                    if self.macro_events["events"][events]["pressed"]:
                                        self.keyboardControl.press(keyToPress)
                                        if keyToPress not in keyToUnpress:
                                            keyToUnpress.append(keyToPress)
                                    else:
                                        self.keyboardControl.release(keyToPress)
                        except ValueError as e:
                            messagebox.showerror("Error",
                                                 f"Error during playback \"{e}\". Please open an issue on Github.")
                            self.stop_playback()
                        except Exception as e:
                            messagebox.showerror("Error",
                                                 f"An unexpected error occurred\n{e}")
                            self.stop_playback()

            repeat_count += 1

            if userSettings["Playback"]["Repeat"]["Delay"] > 0:
                if is_infinite or repeat_count < repeat_times:
                    if self._playback_cancel.wait(userSettings["Playback"]["Repeat"]["Delay"]):
                        self.unPressEverything(keyToUnpress)
                        return

        self.unPressEverything(keyToUnpress)
        if userSettings["Playback"]["Repeat"]["Interval"] == 0 and userSettings["Playback"]["Repeat"]["For"] == 0 and repeat_count:
            self.stop_playback()
            if userSettings["Minimization"]["When_Playing"]:
                self.main_app.deiconify()

    def unPressEverything(self, keyToUnpress):
        for key in keyToUnpress:
            self.keyboardControl.release(key)
        self.mouseControl.release(Button.left)
        self.mouseControl.release(Button.right)
        self.mouseControl.release(Button.middle)

    def stop_playback(self, playback_stopped_manually=False):
        self._playback_cancel.set()
        self.playback = False
        if not playback_stopped_manually:
            print("playback stopped")
        else:
            print("playback stopped manually")
        userSettings = self.user_settings.settings_dict
        self.main_app.recordBtn.configure(state=NORMAL)
        self.main_app.playBtn.configure(
            image=self.main_app.playImg, command=self.start_playback
        )
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_text"], state=NORMAL)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["save_as_text"], state=NORMAL)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["new_text"], state=NORMAL)
        self.main_menu.file_menu.entryconfig(self.main_app.text_content["file_menu"]["load_text"], state=NORMAL)
        if userSettings["Minimization"]["When_Playing"]:
            self.main_app.deiconify()
        if playback_stopped_manually:
            try:
                self.main_app.after(100, self.main_app._bring_main_window_forward)
            except Exception:
                pass

    def import_record(self, record):
        self.macro_events = record

    def __record_event(self,e):
        e['timestamp'] = self.event_delta_time
        self.macro_events["events"].append(e)

    def __get_event_delta_time(self):
        timenow=time()
        self.event_delta_time = timenow - self.time
        self.time=timenow

    def __on_move(self, x, y):
        self.__get_event_delta_time()
        self.__record_event(
            {"type": "cursorMove", "x": x, "y": y}
        )
        if self.showEventsOnStatusBar:
            self.main_app.status_text.configure(text=f"cursorMove {int(x)} {int(y)}")

    def __on_click(self, x, y, button, pressed):
        self.__get_event_delta_time()
        button_event = "unknownButtonClickEvent"
        if button == Button.left:
            button_event = "leftClickEvent"
        elif button == Button.right:
            button_event = "rightClickEvent"
        elif button == Button.middle:
            button_event = "middleClickEvent"
        self.__record_event(
            {
                "type": button_event,
                "x": x,
                "y": y,
                "pressed": pressed
            }
        )
        if self.showEventsOnStatusBar:
            self.main_app.status_text.configure(text=f"{button_event} {int(x)} {int(y)} {pressed}")

    def __on_scroll(self, x, y, dx, dy):
        self.__get_event_delta_time()
        self.__record_event(
            {"type": "scrollEvent", "dx": dx, "dy": dy}
        )
        if self.showEventsOnStatusBar:
            self.main_app.status_text.configure(text=f"scrollEvent {int(dx)} {int(dy)}")

    def _is_hotkey_key(self, key_pressed):
        """True for keys bound to a macro hotkey, which must stay out of the recording."""
        if not (self.record or self.playback) or key_pressed is None:
            return False
        target = normalize_key(key_pressed)
        # Fn is only ever a modifier used to reach an F-key or media key, so it
        # must never become an event of its own in the macro.
        if target in FN_KEY_CODES:
            return True
        try:
            hotkeys = self.user_settings.settings_dict.get("Hotkeys", {})
        except Exception:
            return False
        for name in ("Record_Start", "Record_Stop", "Playback_Start", "Playback_Stop"):
            for bound in hotkeys.get(name) or []:
                if normalize_key(bound) == target:
                    return True
        return False

    def __on_press(self, key):
        self.__get_event_delta_time()
        keyPressed = getKeyPressed(self.keyboard_listener, key)
        if self._is_hotkey_key(keyPressed):
            return
        if self.keyboardBeingListened:
            self.__record_event(
                {
                    "type": "keyboardEvent",
                    "key": keyPressed,
                    "pressed": True,
                }
            )
        if self.showEventsOnStatusBar:
            self.main_app.status_text.configure(text=f"Key: {_fmt_key(keyPressed)} pressed")

    def __on_release(self, key):
        self.__get_event_delta_time()
        keyPressed = getKeyPressed(self.keyboard_listener, key)
        if self._is_hotkey_key(keyPressed):
            return
        if self.keyboardBeingListened:
            self.__record_event(
                {
                    "type": "keyboardEvent",
                    "key": keyPressed,
                    "pressed": False,
                }
            )
        if self.showEventsOnStatusBar:
            self.main_app.status_text.configure(text=f"Key: {_fmt_key(keyPressed)} released")
