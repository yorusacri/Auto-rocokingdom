<p align="center">
  <img src="web/icon.svg" width="96" height="96" alt="Auto-Roco"><br>
</p>

<h1 align="center">Auto-Roco</h1>
<p align="center"><strong>洛克王国：世界</strong> · 游戏自动化助手</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue?logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.10+-informational?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

基于 OpenCV 模板匹配的桌面客户端，自动识别战斗状态并模拟键盘/鼠标操作。Interception 内核驱动级输入，游戏无法感知。

<p align="center">
  <img src="https://img.shields.io/badge/输入方案-Interception_驱动-amber" alt="Input">
  &nbsp;
  <img src="https://img.shields.io/badge/匹配引擎-OpenCV_Canny-cyan" alt="Engine">
</p>

---

## 📥 下载

从 [Releases](../../releases) 下载免安装版本（Windows），解压后以**管理员身份**运行：

| 版本 | 说明 |
|------|------|
| **auto-roco-client-lite.zip** | 精简版，不含精灵识别 |
| **auto-roco-client-full.zip** | 完整版，含 EasyOCR 精灵名称识别 |

> 需先安装 [Interception 驱动](https://github.com/oblitum/Interception/releases/tag/v1.0.1) 并重启电脑。

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔍 **智能模式** | 每场战斗自动判定污染/普通，按配置执行聚能/逃跑/技能1+聚能/不操作 |
| ⚾ **自动丢球** | 非战斗状态检测画面自动丢球，窗口必须在前台 |
| 🤝 **同行确认** | 检测到重新同行请求自动按 `F` |
| 📊 **污染日志** | 污染精灵名称记录到 CSV（需 full 版 EasyOCR） |
| 🎮 **桌面客户端** | 暗色面板 GUI，实时状态 + 日志，一键暂停/恢复 |
| ⚙️ **设置面板** | 匹配阈值 + 检测间隔可调，自动保存 |
| 🔒 **驱动输入** | Interception 内核级模拟，游戏无法检测 |

### 客户端界面

- **暂停按钮**（头部）：一键暂停/恢复，空格键快捷操作。暂停后显示红色停止按钮。
- **状态面板**（左侧）：战斗场次、污染次数、实时检测分数。
- **引擎日志**（右侧）：终端风格，只显示程序行为（`待机中...` / `战斗中 \| 触发`），不刷分数。
- **窗口选择器**：刷新扫描匹配窗口，单选后热切换。
- **设置**（右上齿轮）：阈值、间隔滑块，保存到 `user_prefs.json`。
- **配置持久化**：模式和行为选择自动记忆。

---

## 📖 使用

### 从源码运行

```bash
# 1. 安装 uv（无需预装 Python）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 以管理员身份打开终端，进入项目目录

# 3. 安装依赖
uv sync

# 4.（可选）安装精灵识别
uv sync --extra easyocr

# 5. 启动客户端
uv run main.py --gui
```

### 从 exe 运行

1. 安装 [Interception 驱动](https://github.com/oblitum/Interception/releases/tag/v1.0.1)，重启电脑
2. 下载 `auto-roco-client-*.zip`，解压
3. 右键 `auto-roco-client-*.exe` → **以管理员身份运行**

---

## ⚙️ 配置

`user_prefs.json`（exe 同目录，自动生成）：

| 参数 | 默认 | 说明 |
|------|------|------|
| `match_threshold` | 0.40 | 模板匹配阈值，越低越灵敏 |
| `poll_interval_sec` | 2.0 | 检测间隔（秒），最大 5.0 |
| `gui_mode` | `smart` | 默认模式 |
| `gui_pollute_action` | `gather` | 污染战斗行为 |
| `gui_normal_action` | `escape` | 普通战斗行为 |

GUI 设置面板可直接调整阈值和间隔，无需手动编辑文件。

---

## ⚠️ 注意事项

- **推荐分辨率**：2560x1600 或 2560x1440（2K），低分辨率会降低识别精度
- **窗口不能最小化**，否则截图失效
- **键盘和鼠标操作需窗口在前台**
- 可在当前分辨率重新截取 `templates/` 中的模板图进行适配

---

## ⚠️ 免责声明

本工具仅供图像识别算法研究及技术交流。使用辅助脚本可能违反游戏服务协议，存在账号风险。**由此产生的一切后果由使用者本人承担。** 本脚本仅模拟正常视觉观察和外设输入，不涉及内存修改、封包篡改等非法行为。

---

<p align="center">
  <sub>有问题或建议请提 <a href="../../issues">Issue</a> | 如果对你有帮助欢迎点个 ⭐ Star</sub>
</p>
