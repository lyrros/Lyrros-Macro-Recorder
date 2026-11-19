from contextlib import contextmanager
from sys import platform


def prepare_pynput_keyboard_listener():
    """Avoid a Carbon keyboard-layout lookup from pynput's worker thread."""
    if platform != "darwin":
        return

    from pynput.keyboard import _darwin as mac_keyboard

    @contextmanager
    def listener_keycode_context():
        # pynput's macOS listener does not use this context when decoding
        # events; it reads the Unicode string from each Quartz keyboard event.
        # The Carbon TIS lookup here can abort on newer macOS when called from
        # the listener's background thread.
        yield (None, None)

    mac_keyboard.keycode_context = listener_keycode_context
