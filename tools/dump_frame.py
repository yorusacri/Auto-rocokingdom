"""输出游戏当前帧的 preprocess 结果，用于与模板图对比调试。

用法：uv run tools/dump_frame.py
输出目录：template_debug/（与 dump_templates.py 共用）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

from config import CONFIG
from core.capture import capture_window_bgr
from core.vision import preprocess
from core.window import find_window_by_keyword, get_client_rect_on_screen


def main():
    hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
    if hwnd is None:
        print(f"未找到游戏窗口: {CONFIG.window_title_keyword}")
        return

    left, top, width, height = get_client_rect_on_screen(hwnd)
    print(f"窗口尺寸: {width}x{height}")

    full_bgr = capture_window_bgr(hwnd)

    # 提取 ROI（与 engine 相同）
    roi_l = max(0, min(width - 1, int(width * CONFIG.roi_left_ratio)))
    roi_t = max(0, min(height - 1, int(height * CONFIG.roi_top_ratio)))
    roi_w = max(1, min(width - roi_l, int(width * CONFIG.roi_width_ratio)))
    roi_h = max(1, min(height - roi_t, int(height * CONFIG.roi_height_ratio)))
    roi_bgr = full_bgr[roi_t:roi_t + roi_h, roi_l:roi_l + roi_w]

    # 上半屏 ROI（战斗结束检测用）
    end_l = max(0, min(width - 1, int(width * 0.5)))
    end_t = 0
    end_w = max(1, min(width - end_l, int(width * 0.5)))
    end_h = max(1, min(height - end_t, int(height * 0.5)))
    end_bgr = full_bgr[end_t:end_t + end_h, end_l:end_l + end_w]

    # 中心 ROI（同行检测用）
    cr = CONFIG.reconnect_center_roi
    cl = max(0, min(width - 1, int(width * cr[0])))
    ct = max(0, min(height - 1, int(height * cr[1])))
    cw = max(1, min(width - cl, int(width * cr[2])))
    ch = max(1, min(height - ct, int(height * cr[3])))
    center_bgr = full_bgr[ct:ct + ch, cl:cl + cw]

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template_debug")
    os.makedirs(out_dir, exist_ok=True)

    # 保存原始截图
    cv2.imwrite(os.path.join(out_dir, "frame_full.png"), full_bgr)
    print(f"  frame_full.png        {width}x{height}  [原始BGR]")

    # 保存动作/类型检测 ROI 的 preprocess 结果
    roi_processed = preprocess(roi_bgr)
    cv2.imwrite(os.path.join(out_dir, "frame_roi_action.png"), roi_processed)
    print(f"  frame_roi_action.png  {roi_w}x{roi_h}  [preprocess]  (动作+类型检测 ROI)")

    # 保存战斗结束 ROI 的 preprocess 结果
    end_processed = preprocess(end_bgr)
    cv2.imwrite(os.path.join(out_dir, "frame_roi_end.png"), end_processed)
    print(f"  frame_roi_end.png     {end_w}x{end_h}  [preprocess]  (战斗结束检测 ROI)")

    # 保存中心 ROI 的灰度图（同行检测用，不走 preprocess）
    center_gray = cv2.cvtColor(center_bgr, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.join(out_dir, "frame_roi_center.png"), center_gray)
    print(f"  frame_roi_center.png  {cw}x{ch}  [grayscale]   (同行检测 ROI)")

    print(f"\n已输出到 {out_dir}/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
    input("\n按回车退出...")
