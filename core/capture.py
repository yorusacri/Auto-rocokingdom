import ctypes

import cv2
import numpy as np
import win32con
import win32gui
import win32ui


_printwindow_failed_logged = False
_bitmap_size_mismatch_logged = False


def capture_window_bgr(hwnd: int) -> np.ndarray:
    """
    通过 Windows API 直接抓取窗口内容，即使窗口被遮挡。
    """
    global _printwindow_failed_logged, _bitmap_size_mismatch_logged

    client_rect = win32gui.GetClientRect(hwnd)
    client_w = client_rect[2] - client_rect[0]
    client_h = client_rect[3] - client_rect[1]

    if client_w <= 0 or client_h <= 0:
        if not _bitmap_size_mismatch_logged:
            print(f"[诊断] 窗口尺寸异常: {client_w}x{client_h}，hwnd={hwnd}")
            _bitmap_size_mismatch_logged = True
        return np.zeros((1, 1, 3), dtype=np.uint8)

    hwndDC = win32gui.GetDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, client_w, client_h)

    saveDC.SelectObject(saveBitMap)

    try:
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

        if result != 1:
            if not _printwindow_failed_logged:
                print(f"[诊断] PrintWindow 失败 (hwnd={hwnd})，已回退到 BitBlt")
                _printwindow_failed_logged = True
            saveDC.BitBlt((0, 0), (client_w, client_h), mfcDC, (0, 0), win32con.SRCCOPY)

        signedIntsArray = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')

        expected_size = client_h * client_w * 4
        if len(img) != expected_size:
            if not _bitmap_size_mismatch_logged:
                print(f"[诊断] 位图数据不匹配: 期望 {expected_size} 字节, 实际 {len(img)} 字节")
                _bitmap_size_mismatch_logged = True
            img = np.zeros(expected_size, dtype='uint8')

        img.shape = (client_h, client_w, 4)
    finally:
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
