from sys import platform

_MODIFIER_NORMALIZE = {
    "Key.ctrl_l":  "Key.ctrl",
    "Key.ctrl_r":  "Key.ctrl",
    "Key.shift_l": "Key.shift",
    "Key.shift_r": "Key.shift",
    "Key.alt_l":   "Key.alt",
    "Key.alt_r":   "Key.alt",
    "Key.cmd_l":   "Key.cmd",
    "Key.cmd_r":   "Key.cmd",
}


def normalize_key(key_str):
    if key_str is None:
        return None
    return _MODIFIER_NORMALIZE.get(key_str, key_str)


def getKeyPressed(keyboardListener, key):
    """Return right key. canonical() prevents from weird characters to show up with ctrl active. Like ctrl + d,
    pynput will not print Key.ctrl and d, it will print Key.ctrl and a weird character"""
    if "Key." in str(key):
        keyPressed = str(key)
    else:
        if platform.lower() == "win32":
            keyPressed_list = list(str(keyboardListener.canonical(key)))
        else:
            keyPressed_list = list(str(key))
        if keyPressed_list[0] != "<":
            keyPressed_list[0] = ""
            keyPressed_list[-1] = ""
        keyPressed = "".join(keyPressed_list)
        if platform.lower() == "darwin":
            if keyPressed == "\\x03":
                keyPressed = "Key.enter"
            if keyPressed == "\\x1b":
                keyPressed = None
        elif platform.lower() == "linux":
            if keyPressed == "'^'":
                keyPressed = "^"
    return keyPressed


def resolve_key_for_playback(raw_key):
    if raw_key is None:
        return None
    from pynput.keyboard import Key, KeyCode
    from utils.keys import vk_nb
    s = str(raw_key).strip()
    if not s:
        return None
    if s in vk_nb:
        return vk_nb[s]
    if s.startswith("<") and s.endswith(">") and s[1:-1].isdigit():
        return KeyCode.from_vk(int(s[1:-1]))
    if s.startswith("Key."):
        attr = s.split(".", 1)[1]
        if hasattr(Key, attr):
            return getattr(Key, attr)
        base = attr.replace("_l", "").replace("_r", "")
        return getattr(Key, base, None)
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1]
    return s if len(s) == 1 else None
