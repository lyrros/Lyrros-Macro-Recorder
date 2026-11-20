from math import isfinite
from tkinter import BooleanVar, Entry, StringVar, messagebox
from tkinter.ttk import Button, Checkbutton, Frame, Label, Separator
from windows.popup import Popup
from utils.key_names import format_key_name, normalize_key_name

STEP_TYPE_LABELS = {
    "cursorMove": "Move",
    "leftClickEvent": "Left Click",
    "rightClickEvent": "Right Click",
    "middleClickEvent": "Middle Click",
    "scrollEvent": "Scroll",
    "keyboardEvent": "Key",
}
STEP_TYPE_CODES = {label: code for code, label in STEP_TYPE_LABELS.items()}
STEP_TYPES = list(STEP_TYPE_CODES)


class StepEditor(Popup):
    def __init__(self, parent, main_app, step_index=None, existing_step=None):
        title = "Edit Step" if existing_step is not None else "Add Step"
        super().__init__(title, 460, 360, parent)
        self.resizable(False, False)
        self.main_app, self.step_index = main_app, step_index
        ev = dict(existing_step) if existing_step is not None else {
            "type": "leftClickEvent", "x": 0, "y": 0, "pressed": True, "timestamp": 0.1
        }
        event_type = ev.get("type", "leftClickEvent")
        self.type_var = StringVar(value=STEP_TYPE_LABELS.get(event_type, "Left Click"))
        self.x_var = StringVar(value=str(int(ev.get("x", ev.get("dx", 0)))))
        self.y_var = StringVar(value=str(int(ev.get("y", ev.get("dy", 0)))))
        self.key_var = StringVar(value=format_key_name(ev.get("key", "")))
        self.ts_var = StringVar(value=str(round(float(ev.get("timestamp", 0.1)), 3)))
        self.pressed_var = BooleanVar(value=bool(ev.get("pressed", True)))

        Label(self, text=title, font=("Helvetica Neue", 15, "bold")).pack(pady=(16, 3))
        Label(self, text="Choose an action, then set its details and timing", font=("Helvetica Neue", 11), foreground="#9e9e9e").pack(pady=(0, 12))

        choices = Frame(self)
        choices.pack(pady=(0, 6))
        for index, label in enumerate(STEP_TYPES):
            Button(choices, text=label, command=lambda value=label: self._select_type(value)).grid(
                row=index // 3, column=index % 3, padx=4, pady=4
            )

        self.selected_lbl = Label(self, text="", font=("Helvetica Neue", 11, "bold"), foreground="#40C4FF")
        self.selected_lbl.pack(pady=(2, 8))
        Separator(self).pack(fill="x", padx=22, pady=(0, 8))

        details = Frame(self)
        details.pack(padx=24, pady=(0, 4))

        self.xy_frame = Frame(details)
        self.xy_frame.grid(row=0, column=0, columnspan=2, pady=5)
        self.x_label = Label(self.xy_frame, text="X", font=("Helvetica Neue", 11))
        self.x_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.x_entry = self._entry(self.xy_frame, self.x_var, width=8)
        self.x_entry.grid(row=0, column=1, padx=(0, 16))
        self.y_label = Label(self.xy_frame, text="Y", font=("Helvetica Neue", 11))
        self.y_label.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.y_entry = self._entry(self.xy_frame, self.y_var, width=8)
        self.y_entry.grid(row=0, column=3)

        self.key_frame = Frame(details)
        self.key_frame.grid(row=1, column=0, columnspan=2, pady=5)
        Label(self.key_frame, text="Key", font=("Helvetica Neue", 11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.key_entry = self._entry(self.key_frame, self.key_var, width=20)
        self.key_entry.grid(row=0, column=1)
        Label(self.key_frame, text="Use a character or a name like Space, Return, or Command", font=("Helvetica Neue", 9), foreground="#888888").grid(row=1, column=1, sticky="w", pady=(2, 0))

        self.delay_frame = Frame(details)
        self.delay_frame.grid(row=2, column=0, columnspan=2, pady=5)
        Label(self.delay_frame, text="Delay before step (seconds)", font=("Helvetica Neue", 11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ts_entry = self._entry(self.delay_frame, self.ts_var, width=8)
        self.ts_entry.grid(row=0, column=1, sticky="w")

        self.pressed_check = Checkbutton(details, text="Pressed (unchecked means released)", variable=self.pressed_var)
        self.pressed_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 2))

        tracker = Frame(details)
        tracker.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))
        Label(tracker, text="Live cursor:", font=("Helvetica Neue", 11), foreground="#9e9e9e").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.live_xy = Label(tracker, text="0, 0", font=("Courier", 13, "bold"), foreground="#40C4FF", width=13, anchor="w")
        self.live_xy.grid(row=0, column=1, sticky="w")
        Button(tracker, text="Use This Position", width=17, command=self._capture_position).grid(row=0, column=2, padx=(10, 0))

        btns = Frame(self)
        btns.pack(side="bottom", pady=(4, 8))
        Button(btns, text="Save Step", width=11, command=self._save).pack(side="left", padx=4)
        Button(btns, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=4)
        self._update_fields()
        self.bind("<Return>", lambda e: self._capture_position())
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        self.update_idletasks()
        width = 460
        height = max(330, self.winfo_reqheight() + 8)
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = 60
        self.geometry(f"{width}x{height}+{x}+{y}")
        self._track_position()

    def _track_position(self):
        try:
            if not self.winfo_exists():
                return
            self.live_xy.config(text=f"{self.winfo_pointerx()}, {self.winfo_pointery()}")
        except Exception:
            return
        self.after(100, self._track_position)

    def _capture_position(self):
        try:
            self.x_var.set(str(self.winfo_pointerx()))
            self.y_var.set(str(self.winfo_pointery()))
        except Exception:
            pass
        return "break"

    @staticmethod
    def _entry(parent, variable, width):
        return Entry(parent, textvariable=variable, width=width, justify="center", font=("Helvetica Neue", 13), bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff", relief="flat", bd=0, highlightthickness=1, highlightbackground="#454545", highlightcolor="#40C4FF")

    def _select_type(self, label):
        self.type_var.set(label)
        self._update_fields()

    def _update_fields(self):
        label = self.type_var.get()
        self.selected_lbl.config(text=f"Selected: {label}")
        is_key = label == "Key"
        is_scroll = label == "Scroll"
        self.xy_frame.grid_remove()
        if is_key:
            self.key_frame.grid()
        else:
            self.key_frame.grid_remove()
        if is_key or label == "Move":
            self.pressed_check.grid_remove()
        else:
            self.pressed_check.grid()
        if is_scroll:
            self.x_label.config(text="Scroll X")
            self.y_label.config(text="Scroll Y")
        else:
            self.x_label.config(text="X")
            self.y_label.config(text="Y")
        if not is_key:
            self.xy_frame.grid()

    def _save(self):
        t = STEP_TYPE_CODES.get(self.type_var.get(), self.type_var.get())
        try:
            xv = int(float(self.x_var.get() or 0))
            yv = int(float(self.y_var.get() or 0))
            ts = float(self.ts_var.get() or 0.0)
            if not isfinite(ts):
                raise ValueError
            ts = max(0.0, ts)
        except (TypeError, ValueError, OverflowError):
            messagebox.showerror("Invalid step", "Enter valid numbers for the coordinates and delay.", parent=self)
            return
        if t == "cursorMove":
            new_ev = {"type": t, "x": xv, "y": yv, "timestamp": ts}
        elif t == "scrollEvent":
            new_ev = {"type": t, "dx": xv, "dy": yv, "timestamp": ts}
        elif t == "keyboardEvent":
            new_ev = {"type": t, "key": normalize_key_name(self.key_var.get()), "pressed": bool(self.pressed_var.get()), "timestamp": ts}
        else:
            new_ev = {"type": t, "x": xv, "y": yv, "pressed": bool(self.pressed_var.get()), "timestamp": ts}

        events = self.main_app.macro.macro_events.setdefault("events", [])
        if self.step_index is not None and 0 <= self.step_index < len(events):
            events[self.step_index] = new_ev
            self.main_app._pending_select = self.step_index
        else:
            selection = self.main_app.action_list.curselection()
            insert_at = (selection[-1] + 1) if selection else len(events)
            events.insert(insert_at, new_ev)
            self.main_app._pending_select = insert_at
        self.main_app.macro_recorded = bool(events)
        self.main_app.macro_saved = False
        self.main_app._last_ev_sig = None
        if self.main_app.macro_recorded:
            self.main_app.playBtn.configure(state="normal", command=self.main_app.macro.start_playback)
        self.destroy()
