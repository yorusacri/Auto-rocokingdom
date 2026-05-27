import re
import warnings

import cv2
import numpy as np

_ocr_error_logged = False

try:
    import easyocr
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        _reader = easyocr.Reader(["ch_sim", "en"], verbose=False)
except ImportError as e:
    _reader = None
    print(f"[\u8bca\u65ad] EasyOCR \u4e0d\u53ef\u7528: {e}")
    if "easyocr" in str(e).lower():
        print("       easyocr \u672a\u5b89\u88c5\u3002\u5982\u9700 OCR \u7cbe\u7075\u540d\u79f0\u8bc6\u522b\uff0c\u8fd0\u884c: uv sync --extra easyocr")
    elif "torch" in str(e).lower():
        print("       PyTorch \u672a\u5b89\u88c5\u3002\u8fd0\u884c: uv sync --extra easyocr")
except Exception as e:
    _reader = None
    print(f"[\u8b66\u544a] EasyOCR \u521d\u59cb\u5316\u5931\u8d25: {e}")

from config import CONFIG


def _extract_ocr_roi(full_bgr: np.ndarray, width: int, height: int) -> np.ndarray:
    l = max(0, int(width * CONFIG.ocr_roi_left_ratio))
    t = max(0, int(height * CONFIG.ocr_roi_top_ratio))
    w = max(1, min(width - l, int(width * CONFIG.ocr_roi_width_ratio)))
    h = max(1, min(height - t, int(height * CONFIG.ocr_roi_height_ratio)))
    return full_bgr[t:t + h, l:l + w]


def _preprocess(bgr_patch: np.ndarray) -> np.ndarray:
    scale_factor = CONFIG.ocr_upscale_factor
    new_w = max(1, int(bgr_patch.shape[1] * scale_factor))
    new_h = max(1, int(bgr_patch.shape[0] * scale_factor))
    return cv2.resize(bgr_patch, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def recognize_spirit_name(full_bgr: np.ndarray, width: int, height: int) -> str:
    global _ocr_error_logged
    if _reader is None:
        return CONFIG.ocr_fallback_text

    try:
        patch = _extract_ocr_roi(full_bgr, width, height)
        processed = _preprocess(patch)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            results = _reader.readtext(processed)

        if not results:
            return CONFIG.ocr_fallback_text

        first_text = results[0][1]
        match = re.match(r"[\u4e00-\u9fff]+", first_text)
        return match.group(0) if match else CONFIG.ocr_fallback_text

    except Exception as e:
        if not _ocr_error_logged:
            print(f"[\u8b66\u544a] OCR \u8bc6\u522b\u5931\u8d25: {e}")
            _ocr_error_logged = True
        return CONFIG.ocr_fallback_text
