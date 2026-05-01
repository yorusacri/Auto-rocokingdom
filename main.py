from config import CONFIG
from core.engine import Engine
from modes import MODE_REGISTRY
from modes.smart import ACTION_OPTIONS, SmartMode


def _action_label(action: str) -> str:
    for _, (key, label) in ACTION_OPTIONS.items():
        if key == action:
            return label
    return action


def _prompt_action(battle_type: str, default: str) -> str:
    print(f"\n请选择遇到【{battle_type}】时的行为:")
    for key, (_, label) in ACTION_OPTIONS.items():
        marker = "（默认）" if ACTION_OPTIONS[key][0] == default else ""
        print(f"  {key}: {label}{marker}")
    choice = input(f"请输入选项 ({'/'.join(ACTION_OPTIONS.keys())}): ").strip()
    if choice in ACTION_OPTIONS:
        return ACTION_OPTIONS[choice][0]
    return default


def main() -> None:
    print("\n请选择运行模式:")
    for key, cls in sorted(MODE_REGISTRY.items()):
        mode = cls()
        print(f"  {key}: {mode.label}")
    print("有问题或新功能建议请提 issue。如果这个项目对你有帮助，欢迎点个 Star 支持一下。")
    print("\n[提示] 脚本支持自适应分辨率，推荐使用 2K（2560x1600 或 2560x1440）以获得更高识别精度。")
    print("分辨率越低 Score 可能越低；若识别异常，可在当前分辨率下重截 templates 进行适配。")
    print('[提示] 逃跑模式使用物理点击，请确保"是"按钮露出且不被其他窗口遮挡。')

    choices = "/".join(sorted(MODE_REGISTRY.keys()))
    choice = input(f"请输入选项 ({choices}): ").strip()

    if choice == "4":
        pollute_action = "gather"
        normal_action = "escape"

        print("\n当前智能模式默认配置:")
        print(f"  污染战斗 → {_action_label(pollute_action)}")
        print(f"  普通战斗 → {_action_label(normal_action)}")

        customize = input("是否修改配置？(y/N): ").strip().lower()
        if customize == "y":
            pollute_action = _prompt_action("污染战斗", pollute_action)
            normal_action = _prompt_action("普通战斗", normal_action)
            print(f"\n已应用自定义配置:")
            print(f"  污染战斗 → {_action_label(pollute_action)}")
            print(f"  普通战斗 → {_action_label(normal_action)}")

        mode = SmartMode(pollute_action=pollute_action, normal_action=normal_action)
    else:
        mode_cls = MODE_REGISTRY.get(choice, MODE_REGISTRY["1"])
        mode = mode_cls()

    # 输入方式选择
    print("\n请选择输入方式:")
    print("  1: sendinput（拟真度高，需游戏在前台）（默认）")
    print("  2: postmessage（可后台，拟真度低）")
    input_choice = input("请输入选项 (1/2): ").strip()
    if input_choice == "2":
        CONFIG.input_method = "postmessage"
    else:
        CONFIG.input_method = "sendinput"

    Engine(mode).run()


if __name__ == "__main__":
    main()
