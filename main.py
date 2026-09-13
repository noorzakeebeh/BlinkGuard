"""
BlinkGuard entry point.

Run with:
    python main.py
"""
import sys
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
