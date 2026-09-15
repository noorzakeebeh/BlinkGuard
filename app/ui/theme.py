"""
Simple stylesheet-based theming for Light / Dark / System modes.
System mode follows the OS palette via Qt's own style; Light/Dark apply an
explicit QSS stylesheet so both modes look intentional rather than default.
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

LIGHT_QSS = """
QWidget { background-color: #F7F8FA; color: #1C1E21; font-family: 'Segoe UI', sans-serif; }
QMainWindow { background-color: #F7F8FA; }
#SideNav { background-color: #FFFFFF; border-right: 1px solid #E4E6EA; }
#SideNavButton { text-align: left; padding: 10px 16px; border: none; border-radius: 8px;
    font-size: 14px; color: #4B4F56; }
#SideNavButton:hover { background-color: #EDEFF3; }
#SideNavButton[active="true"] { background-color: #E8F0FE; color: #1A56DB; font-weight: 600; }
QFrame#Card { background-color: #FFFFFF; border-radius: 14px; border: 1px solid #ECEEF1; }
QLabel#StatValue { font-size: 26px; font-weight: 700; color: #1C1E21; }
QLabel#StatLabel { font-size: 12px; color: #767B85; }
QLabel#PageTitle { font-size: 20px; font-weight: 700; }
QPushButton#Primary { background-color: #1A56DB; color: white; border-radius: 8px;
    padding: 8px 16px; font-weight: 600; }
QPushButton#Primary:hover { background-color: #1546B0; }
QPushButton#Secondary { background-color: #EDEFF3; color: #1C1E21; border-radius: 8px;
    padding: 8px 16px; }
QPushButton#Secondary:hover { background-color: #DEE1E6; }
"""

DARK_QSS = """
QWidget { background-color: #16181C; color: #E6E7EA; font-family: 'Segoe UI', sans-serif; }
QMainWindow { background-color: #16181C; }
#SideNav { background-color: #1D1F24; border-right: 1px solid #2A2D33; }
#SideNavButton { text-align: left; padding: 10px 16px; border: none; border-radius: 8px;
    font-size: 14px; color: #B7BAC1; }
#SideNavButton:hover { background-color: #262A31; }
#SideNavButton[active="true"] { background-color: #1E2F55; color: #7FA8FF; font-weight: 600; }
QFrame#Card { background-color: #1D1F24; border-radius: 14px; border: 1px solid #2A2D33; }
QLabel#StatValue { font-size: 26px; font-weight: 700; color: #F2F3F5; }
QLabel#StatLabel { font-size: 12px; color: #9298A3; }
QLabel#PageTitle { font-size: 20px; font-weight: 700; }
QPushButton#Primary { background-color: #3B6FE0; color: white; border-radius: 8px;
    padding: 8px 16px; font-weight: 600; }
QPushButton#Primary:hover { background-color: #345FC0; }
QPushButton#Secondary { background-color: #262A31; color: #E6E7EA; border-radius: 8px;
    padding: 8px 16px; }
QPushButton#Secondary:hover { background-color: #30343C; }
"""


def apply_theme(app: QApplication, mode: str):
    mode = (mode or "system").lower()
    if mode == "light":
        app.setStyleSheet(LIGHT_QSS)
    elif mode == "dark":
        app.setStyleSheet(DARK_QSS)
    else:
        # "system": detect via palette lightness heuristic, else fall back to light
        app.setStyleSheet("")
        palette = app.palette()
        bg = palette.color(QPalette.ColorRole.Window)
        is_dark = bg.lightness() < 128
        app.setStyleSheet(DARK_QSS if is_dark else LIGHT_QSS)
