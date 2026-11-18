import sys
if sys.platform == "darwin":
    try:
        import ApplicationServices
        ApplicationServices.AXIsProcessTrusted()
    except Exception:
        pass

from windows import MainApp

if __name__ == "__main__":
    MainApp()
