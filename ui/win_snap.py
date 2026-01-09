from __future__ import annotations

import sys

if sys.platform == "win32":
    import ctypes

    GWL_STYLE = -16
    WS_THICKFRAME = 0x00040000
    WS_MAXIMIZEBOX = 0x00010000
    WS_MINIMIZEBOX = 0x00020000
    WS_SYSMENU = 0x00080000
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    user32 = ctypes.WinDLL("user32", use_last_error=True)


    def apply_snap_styles(hwnd: int) -> None:
        """Enable Windows snap/resize for frameless windows."""
        if not hwnd:
            return
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style |= WS_THICKFRAME | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )
else:

    def apply_snap_styles(hwnd: int) -> None:
        return
