from config import CONFIG, load_prefs, save_prefs
from core.engine import Engine
from core.window import list_windows_by_keyword
from modes import MODE_REGISTRY
from modes.smart import ACTION_OPTIONS, SmartMode


ACTION_LABELS = {key: label for key, (action, label) in ACTION_OPTIONS.items()}
ACTION_VALUES = {action: label for key, (action, label) in ACTION_OPTIONS.items()}


def _select_window() -> int | None:
    keyword = CONFIG.window_title_keyword
    windows = list_windows_by_keyword(keyword)

    if not windows:
        print(f"\n[错误] 未找到包含 \"{keyword}\" 的窗口，请确认游戏已启动。")
        return None

    print(f"\n找到 {len(windows)} 个匹配 \"{keyword}\" 的窗口:\n")
    for i, (hwnd, title, (x, y, w, h)) in enumerate(windows, 1):
        print(f"  {i}. {title}")
        print(f"     句柄: {hwnd}  位置: ({x}, {y})  尺寸: {w}x{h}\n")

    if len(windows) == 1:
        hwnd, title, (_, _, w, h) = windows[0]
        print(f"仅找到一个窗口，自动选择: {title}\n")
    else:
        while True:
            sel = input(f"请选择窗口 (1-{len(windows)}): ").strip()
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(windows):
                    break
            except ValueError:
                pass
            print(f"输入无效，请输入 1-{len(windows)} 的数字")

        hwnd, title, _ = windows[idx]
        print(f"\n已选择: {title}\n")

    return hwnd


def _action_label(action: str) -> str:
    return ACTION_VALUES.get(action, action)


def _prompt_action(battle_type: str, default: str) -> str:
    print(f"\n请选择遇到【{battle_type}】时的行为:")
    for key, (action, label) in ACTION_OPTIONS.items():
        marker = "（默认）" if action == default else ""
        print(f"  {key}: {label}{marker}")
    choice = input(f"请输入选项 ({'/'.join(ACTION_OPTIONS.keys())}): ").strip()
    if choice in ACTION_OPTIONS:
        return ACTION_OPTIONS[choice][0]
    return default


def main() -> None:
    prefs = load_prefs()

    print("\n请选择运行模式:")
    for key, cls in sorted(MODE_REGISTRY.items()):
        mode = cls()
        print(f"  {key}: {mode.label}")
    print("有问题或新功能建议请提 issue。如果这个项目对你有帮助，欢迎点个 Star 支持一下。")
    print("\n[提示] 脚本支持自适应分辨率，推荐使用 2K（2560x1600 或 2560x1440）以获得更高识别精度。")
    print("分辨率越低 Score 可能越低；若识别异常，可在当前分辨率下重截 templates 进行适配。")

    choices = "/".join(sorted(MODE_REGISTRY.keys()))
    choice = input(f"请输入选项 ({choices}): ").strip()

    if choice == "1":
        pollute_action = prefs.get("pollute_action", "gather")
        normal_action = prefs.get("normal_action", "escape")

        print("\n当前智能模式配置:")
        print(f"  污染战斗 → {_action_label(pollute_action)}")
        print(f"  普通战斗 → {_action_label(normal_action)}")

        customize = input("是否修改配置？(y/N): ").strip().lower()
        if customize == "y":
            pollute_action = _prompt_action("污染战斗", pollute_action)
            normal_action = _prompt_action("普通战斗", normal_action)
            print(f"\n已应用自定义配置:")
            print(f"  污染战斗 → {_action_label(pollute_action)}")
            print(f"  普通战斗 → {_action_label(normal_action)}")

        prefs["pollute_action"] = pollute_action
        prefs["normal_action"] = normal_action
        mode = SmartMode(pollute_action=pollute_action, normal_action=normal_action)
    else:
        mode_cls = MODE_REGISTRY.get(choice, MODE_REGISTRY["1"])
        mode = mode_cls()

    hwnd = _select_window()
    if hwnd is None:
        return

    Engine(mode, hwnd=hwnd).run()


if __name__ == "__main__":
    main()
