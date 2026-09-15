"""
BlinkGuard entry point.

Run with:
    python main.py
"""
import sys

# On Windows, if the display scale is above 100% (very common on laptops),
# an app that hasn't declared itself "DPI-aware" gets bitmap-stretched by
# Windows instead of rendered natively at the correct resolution -- this is
# what makes small text (like a decimal point) and icons look blurry or
# missing. Declaring awareness here fixes that.
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
    except Exception:
        pass

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # keep running in tray when window is closed

    try:
        window = MainWindow(app)
    except Exception as e:
        QMessageBox.critical(None, APP_NAME, f"BlinkGuard failed to start:\n{e}")
        sys.exit(1)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
