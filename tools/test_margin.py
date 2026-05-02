"""诊断脚本：监控战斗类型判定的过渡帧行为。

核心逻辑：模拟 engine.py 中战斗开始的那一帧，
当 action_score >= threshold（战斗已触发）但 capture/pollute 分数都还很低时，
就是分类不稳定的"可疑帧"。

用法：uv run tools/test_margin.py
按 Ctrl+C 停止，会输出统计摘要。
"""

import os
import sys
import time as _time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from core.capture import capture_window_bgr
from core.vision import (
    best_match_score,
    load_templates,
    normalize_template_name,
    preprocess,
)
from core.window import find_window_by_keyword, get_client_rect_on_screen

_ACTION_EXCLUDE_KEYS = {
    "yes.png",
    "qiudaidai.png",
    "capture.png",
    "pollute_capture.png",
}


def main():
    templates = load_templates()
    capture_key = normalize_template_name(CONFIG.capture_template_name)
    pollute_key = normalize_template_name(CONFIG.pollute_capture_template_name)

    print("=== 战斗类型判定过渡帧诊断 ===")
    print(f"参考分辨率: {CONFIG.ref_width}x{CONFIG.ref_height}")
    print(f"动作阈值: {CONFIG.match_threshold}")
    print(f"类型分数门槛: 0.30")
    print(f"类型差值门槛: 0.05")
    print("按 Ctrl+C 停止\n")
    print(f"{'时间':>10} {'act_max':>8} {'capture':>8} {'pollute':>8} {'差值':>8} {'判定':>6} {'状态':>8}")
    print("-" * 64)

    total_frames = 0
    suspect_frames = 0  # 动作已触发但类型未分化
    history = []

    try:
        while True:
            hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
            if hwnd is None:
                print("[警告] 未找到游戏窗口")
                _time.sleep(2)
                continue

            left, top, width, height = get_client_rect_on_screen(hwnd)
            if width <= 0 or height <= 0:
                _time.sleep(1)
                continue

            scale = width / CONFIG.ref_width
            full_bgr = capture_window_bgr(hwnd)

            # ROI: bottom-right quarter (same as engine)
            roi_l = int(width * CONFIG.roi_left_ratio)
            roi_t = int(height * CONFIG.roi_top_ratio)
            roi_w = int(width * CONFIG.roi_width_ratio)
            roi_h = int(height * CONFIG.roi_height_ratio)
            roi_l = max(0, min(width - 1, roi_l))
            roi_t = max(0, min(height - 1, roi_t))
            roi_w = max(1, min(width - roi_l, roi_w))
            roi_h = max(1, min(height - roi_t, roi_h))

            frame_bgr = full_bgr[roi_t:roi_t + roi_h, roi_l:roi_l + roi_w]
            frame_processed = preprocess(frame_bgr)

            _, _, _, all_matches = best_match_score(frame_processed, templates, scale=scale)

            cap_score = 0.0
            pol_score = 0.0
            action_max = -1.0
            for name, score in all_matches:
                key = normalize_template_name(name)
                if key == capture_key:
                    cap_score = score
                elif key == pollute_key:
                    pol_score = score
                elif key not in _ACTION_EXCLUDE_KEYS:
                    if score > action_max:
                        action_max = score

            total_frames += 1
            diff = pol_score - cap_score
            verdict = "污染" if diff > 0 else "普通"

            # 可疑帧 = 动作模板已触发战斗 + 两个类型分数都低 + 差值小
            action_triggered = action_max >= CONFIG.match_threshold
            type_undecided = cap_score < 0.30 and pol_score < 0.30
            low_margin = abs(diff) < 0.05

            frame_status = ""
            if action_triggered and type_undecided:
                frame_status = "⚠可疑"
                suspect_frames += 1
            elif action_triggered and low_margin:
                frame_status = "~近似"
            elif not action_triggered:
                frame_status = ""

            ts = _time.strftime("%H:%M:%S")
            print(f"{ts:>10} {action_max:>8.3f} {cap_score:>8.3f} {pol_score:>8.3f} {diff:>+8.3f} {verdict:>6} {frame_status:>8}")

            history.append((_time.time(), action_max, cap_score, pol_score, verdict, frame_status))

            _time.sleep(0.3)

    except KeyboardInterrupt:
        pass

    # 统计摘要
    print("\n" + "=" * 64)
    print("=== 统计摘要 ===")
    print(f"总帧数: {total_frames}")
    print(f"可疑帧（动作已触发 + 类型未分化）: {suspect_frames}")

    if total_frames > 0:
        print(f"可疑帧占比: {suspect_frames / total_frames * 100:.1f}%")

    # 统计触发帧中判定翻转次数
    triggered = [h for h in history if h[1] >= CONFIG.match_threshold]
    flips = 0
    for i in range(1, len(triggered)):
        if triggered[i][4] != triggered[i - 1][4]:
            flips += 1
    print(f"触发帧中判定翻转: {flips} 次（共 {len(triggered)} 个触发帧）")

    if suspect_frames > 0:
        print(f"\n⚠ 在 {suspect_frames} 帧中，动作模板已触发但类型分数都低于 0.30")
        print("  这些帧的分类结果完全取决于噪声，是问题1的根因")

    # 输出可疑帧详情
    suspect_list = [h for h in history if h[5] == "⚠可疑"]
    if suspect_list:
        print(f"\n可疑帧详情 (共 {len(suspect_list)} 帧，最多显示 20):")
        base_time = suspect_list[0][0]
        for t, act, cap, pol, verdict, _ in suspect_list[:20]:
            print(f"  t+{t - base_time:6.1f}s  act={act:.3f}  capture={cap:.3f}  pollute={pol:.3f}  →{verdict}")


if __name__ == "__main__":
    main()
