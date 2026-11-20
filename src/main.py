import os
import sys
import traceback
from datetime import datetime

from windows import MainApp

ERROR_LOG = os.path.join(os.path.expanduser("~"), "Desktop", "lyrro_errors.log")


class LoggedMainApp(MainApp):
    """Records Tk callback exceptions, which otherwise vanish or just beep."""

    def report_callback_exception(self, exc_type, exc_value, exc_tb):
        try:
            with open(ERROR_LOG, "a", encoding="utf-8") as handle:
                handle.write("\n==== %s\n" % datetime.now().isoformat(timespec="seconds"))
                traceback.print_exception(exc_type, exc_value, exc_tb, file=handle)
        except Exception:
            pass
        try:
            traceback.print_exception(exc_type, exc_value, exc_tb)
        except Exception:
            pass


if __name__ == "__main__":
    LoggedMainApp()
