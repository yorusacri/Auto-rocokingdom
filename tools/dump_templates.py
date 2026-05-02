"""输出所有模板经 preprocess 后的图像，按当前游戏窗口分辨率缩放。

用法：uv run tools/dump_templates.py
输出目录：template_debug/
  原始模板:   template_debug/<name>.png
  缩放模板:   template_debug/scaled/<name>.png
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

from config import CONFIG
from core.vision import preprocess
from core.window import find_window_by_keyword, get_client_rect_on_screen


def dump_templates(out_dir: str, scale: float | None):
    template_dir = CONFIG.template_dir
    files = sorted(f for f in os.listdir(template_dir) if f.endswith(".png"))

    for fname in files:
        path = os.path.join(template_dir, fname)
        raw = cv2.imread(path)
        if raw is None:
            continue

        name_lower = fname.lower()
        if "yes" in name_lower or "qiudaidai" in name_lower:
            processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
            mode = "grayscale"
        else:
            processed = preprocess(raw)
            mode = "canny" if CONFIG.use_edge_match else "gaussian_gray"

        if scale is not None and abs(scale - 1.0) > 0.01:
            new_w = max(1, int(processed.shape[1] * scale))
            new_h = max(1, int(processed.shape[0] * scale))
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_AREA)

        out_path = os.path.join(out_dir, fname)
        cv2.imwrite(out_path, processed)
        h, w = processed.shape[:2]
        print(f"  {fname:<24} {w:>5}x{h:<5}  [{mode}]")


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template_debug")
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== 原始模板 (scale=1.0) ===")
    dump_templates(out_dir, scale=None)

    hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
    if hwnd is None:
        print(f"\n未找到游戏窗口，跳过缩放输出")
        return

    _, _, width, _ = get_client_rect_on_screen(hwnd)
    scale = width / CONFIG.ref_width
    print(f"\n游戏窗口宽度: {width}  scale: {scale:.4f}")

    if abs(scale - 1.0) < 0.01:
        print("scale ≈ 1.0，跳过缩放输出")
        return

    scaled_dir = os.path.join(out_dir, "scaled")
    os.makedirs(scaled_dir, exist_ok=True)
    print(f"\n=== 缩放模板 (scale={scale:.4f}) ===")
    dump_templates(scaled_dir, scale=scale)
    print(f"\n完成，缩放模板在 {scaled_dir}/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
    input("\n按回车退出...")
