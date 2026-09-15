# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for BlinkGuard.
#
# Build with:
#   pyinstaller packaging/blinkguard.spec
#
# Must be run separately on each target OS (Windows / macOS / Linux) --
# PyInstaller does not cross-compile. See DEPLOYMENT_GUIDE.md for the full
# step-by-step process, including the GitHub Actions workflow that builds
# all three automatically.

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

def _icon_or_none(path):
    """PyInstaller errors out if the icon file doesn't exist -- fall back to
    no icon so the build still succeeds before you've added artwork."""
    return path if os.path.isfile(path) else None

# mediapipe and cv2 ship data files (models, .so/.dll/.dylib bits) that
# PyInstaller can't always discover automatically -- collect them explicitly.
mediapipe_datas = collect_data_files("mediapipe")
cv2_datas = collect_data_files("cv2")
# IMPORTANT: cv2's own native DLLs (the actual camera/video backends) are
# NOT picked up by collect_data_files -- they need collect_dynamic_libs, or
# the exe will open the camera "successfully" but never get real frames from
# it (exactly the "Camera disconnected or stopped producing frames" error).
cv2_binaries = collect_dynamic_libs("cv2")
mediapipe_binaries = collect_dynamic_libs("mediapipe")

hidden_imports = (
    collect_submodules("mediapipe")
    + collect_submodules("google.protobuf")
    + ["cv2"]
)

a = Analysis(
    ["../main.py"],
    pathex=["../"],
    binaries=cv2_binaries + mediapipe_binaries,
    datas=mediapipe_datas + cv2_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BlinkGuard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX compresses binaries to shrink the exe, but it's a known cause of
    # OpenCV camera/codec DLLs breaking silently once frozen -- the camera
    # appears to open but never delivers real frames. Disabled for reliability.
    upx=False,
    console=False,          # no terminal window on Windows/macOS
    icon=_icon_or_none("app_icon.ico") if sys.platform.startswith("win") else (
        _icon_or_none("app_icon.icns") if sys.platform == "darwin" else None
    ),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BlinkGuard",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="BlinkGuard.app",
        icon=_icon_or_none("app_icon.icns"),
        bundle_identifier="com.noorzakeebeh.blinkguard",
        info_plist={
            "NSCameraUsageDescription": "BlinkGuard needs camera access to detect blinking locally on your device. No video is ever recorded or uploaded.",
            "LSUIElement": False,
        },
    )
