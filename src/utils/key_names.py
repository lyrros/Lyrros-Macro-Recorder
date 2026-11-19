"""Friendly display names and input aliases for pynput keyboard keys."""

KEY_LABELS = {
    "Key.cmd": "Command", "Key.cmd_l": "Command", "Key.cmd_r": "Command",
    "Key.ctrl": "Control", "Key.ctrl_l": "Control", "Key.ctrl_r": "Control",
    "Key.alt": "Option", "Key.alt_l": "Option", "Key.alt_r": "Option", "Key.alt_gr": "Option",
    "Key.shift": "Shift", "Key.shift_l": "Shift", "Key.shift_r": "Shift",
    "Key.space": "Space", "Key.enter": "Return", "Key.backspace": "Delete",
    "Key.delete": "Forward Delete", "Key.tab": "Tab", "Key.esc": "Escape",
    "Key.caps_lock": "Caps Lock", "Key.up": "Up Arrow", "Key.down": "Down Arrow",
    "Key.left": "Left Arrow", "Key.right": "Right Arrow", "Key.home": "Home",
    "Key.end": "End", "Key.page_up": "Page Up", "Key.page_down": "Page Down",
    "Key.insert": "Insert", "<63>": "Fn", "<179>": "Fn", "<53>": "Escape",
    "<36>": "Return", "<48>": "Tab", "<49>": "Space", "<51>": "Delete",
    "<117>": "Forward Delete", "<123>": "Left Arrow", "<124>": "Right Arrow",
    "<125>": "Down Arrow", "<126>": "Up Arrow", "<122>": "F1", "<120>": "F2",
    "<99>": "F3", "<118>": "F4", "<96>": "F5", "<97>": "F6", "<98>": "F7",
    "<100>": "F8", "<101>": "F9", "<109>": "F10", "<103>": "F11", "<111>": "F12",
}

_ALIASES = {
    "command": "Key.cmd", "cmd": "Key.cmd", "⌘": "Key.cmd",
    "control": "Key.ctrl", "ctrl": "Key.ctrl", "⌃": "Key.ctrl",
    "option": "Key.alt", "alt": "Key.alt", "⌥": "Key.alt",
    "shift": "Key.shift", "⇧": "Key.shift",
    "space": "Key.space", "return": "Key.enter", "enter": "Key.enter",
    "delete": "Key.backspace", "backspace": "Key.backspace",
    "forward delete": "Key.delete", "tab": "Key.tab", "escape": "Key.esc", "esc": "Key.esc",
    "caps lock": "Key.caps_lock", "capslock": "Key.caps_lock",
    "up": "Key.up", "up arrow": "Key.up", "down": "Key.down", "down arrow": "Key.down",
    "left": "Key.left", "left arrow": "Key.left", "right": "Key.right", "right arrow": "Key.right",
    "home": "Key.home", "end": "Key.end", "page up": "Key.page_up", "page down": "Key.page_down",
    "insert": "Key.insert", "fn": "<63>",
}
for _n in range(1, 25):
    _ALIASES[f"f{_n}"] = f"Key.f{_n}"


def format_key_name(value):
    if value is None:
        return ""
    text = str(value).strip().strip("\"'")
    if text in KEY_LABELS:
        return KEY_LABELS[text]
    if text.startswith("Key."):
        return text[4:].replace("_", " ").title()
    if text.startswith("<") and text.endswith(">") and text[1:-1].isdigit():
        return f"Key #{text[1:-1]}"
    return text


def normalize_key_name(value):
    text = str(value or "").strip()
    if not text:
        return "a"
    if text.startswith("Key.") or (text.startswith("<") and text.endswith(">")):
        return text
    return _ALIASES.get(text.casefold(), text)
