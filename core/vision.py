import ctypes
import glob
import os
import sys
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np

from config import CONFIG


@dataclass
class Template:
    name: str
    image: np.ndarray


def normalize_template_name(name: str) -> str:
    return os.path.basename(name).strip().lower()


def normalize_poll_interval(interval: float) -> float:
    if interval <= 0:
        return 5.0
    if interval > 5.0:
        return 5.0
    return interval


def preprocess(image_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    if CONFIG.use_edge_match:
        return cv2.Canny(gray, 100, 200)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return gray


_SYSTEM_DLLS = ("MF.dll", "MFPlat.DLL", "MFReadWrite.dll")
_VCREDIST_DLLS = ("VCRUNTIME140.dll", "VCRUNTIME140_1.dll", "MSVCP140.dll")


def _diagnose_system() -> list[str]:
    """Collect system environment info. Returns list of diagnostic lines."""
    lines = []
    lines.append(f"Python {sys.version}")
    lines.append(f"OpenCV {cv2.__version__}")
    lines.append(f"是否打包: {getattr(sys, 'frozen', False)}")
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        internal_dir = os.path.join(exe_dir, "_internal")
        lines.append(f"exe 目录: {exe_dir}")
        lines.append(f"_internal 存在: {os.path.isdir(internal_dir)}")
        if os.path.isdir(internal_dir):
            png_count = len(glob.glob(os.path.join(internal_dir, "templates", "*.png")))
            web_exists = os.path.isfile(os.path.join(internal_dir, "web", "index.html"))
            lines.append(f"_internal/templates/ 内 PNG 数量: {png_count}")
            lines.append(f"_internal/web/index.html 存在: {web_exists}")
    lines.append(f"模板目录: {CONFIG.template_dir}")

    missing_dlls = []
    for dll in _SYSTEM_DLLS + _VCREDIST_DLLS:
        try:
            ctypes.WinDLL(dll)
        except OSError:
            missing_dlls.append(dll)
    if missing_dlls:
        lines.append(f"DLL 缺失: {', '.join(missing_dlls)}")
    else:
        lines.append("系统 DLL 全部可加载")

    return lines


def _imread_robust(path: str) -> tuple[np.ndarray | None, list[str] | None]:
    """Read an image with fallback from cv2.imread to Python I/O + cv2.imdecode.
    Returns (image, diag_list). diag_list is None when image loaded normally.
    """
    raw = cv2.imread(path)
    if raw is not None:
        return raw, None

    fname = os.path.basename(path)
    fsize = os.path.getsize(path)
    diag = [f"cv2.imread({fname}) 返回 None，文件大小: {fsize} 字节"]

    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        diag.append(f"Python open({fname}) 失败: {e}")
        return None, diag

    arr = np.frombuffer(data, dtype=np.uint8)
    decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if decoded is not None:
        diag.append(f"cv2.imdecode({fname}) 成功 (fallback)，cv2.imread 可能因系统图像组件问题失败")
        return decoded, diag

    diag.append(f"cv2.imdecode({fname}) 也失败，文件可能已损坏")
    if len(data) >= 4:
        sig = data[:4]
        diag.append(f"文件头 4 字节: {sig.hex().upper()} (PNG 应为 89504E47)")
    return None, diag


def load_templates() -> List[Template]:
    diag_lines = _diagnose_system()
    template_dir = CONFIG.template_dir

    if not os.path.isdir(template_dir):
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            internal_dir = os.path.join(exe_dir, "_internal")
            if not os.path.isdir(internal_dir):
                raise FileNotFoundError(
                    f"未找到 _internal 文件夹。\n"
                    f"请将解压后的整个程序文件夹一起运行，不要只拖出 .exe 文件。\n"
                    f"缺少的路径: {internal_dir}"
                )
            raise FileNotFoundError(
                f"模板目录不存在，程序文件可能损坏。\n"
                f"请重新下载解压，或检查杀毒软件是否误删了文件。\n"
                f"缺少的路径: {template_dir}"
            )
        raise FileNotFoundError(
            f"模板目录不存在: {template_dir}\n"
            f"请在程序根目录下创建 templates/ 文件夹并放入 PNG 模板图片。"
        )

    pattern = os.path.join(template_dir, CONFIG.template_pattern)
    paths = sorted(glob.glob(pattern))
    templates: List[Template] = []
    failed_reads: list[str] = []
    _failed_diags: list[str] = []

    for path in paths:
        raw, fdiag = _imread_robust(path)
        if raw is None:
            failed_reads.append(os.path.basename(path))
            if fdiag:
                _failed_diags.extend(fdiag)
            continue
        # If imread succeeded via fallback (imdecode), log the diagnostic once
        if fdiag and not _failed_diags:
            pass  # fallback success diag is informational, not an error

        if "yes" in path.lower():
            processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        else:
            processed = preprocess(raw)

        if "qiudaidai" in path.lower():
            processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

        templates.append(Template(name=os.path.basename(path), image=processed))

    if not templates:
        # Dump full diagnostics into the error message
        diag_text = "\n".join(diag_lines)
        if not paths:
            raise FileNotFoundError(
                f"模板目录存在但未找到任何 PNG 文件。\n"
                f"路径: {template_dir}\n"
                f"请重新下载解压，或检查杀毒软件是否误删了模板文件。\n"
                f"--- 系统诊断 ---\n{diag_text}"
            )
        failed_text = "\n".join(_failed_diags)
        raise FileNotFoundError(
            f"找到 {len(paths)} 个模板文件，但全部无法读取。\n"
            f"模板路径: {template_dir}\n"
            f"失败文件: {', '.join(failed_reads)}\n"
            f"--- 文件加载详情 ---\n{failed_text}\n"
            f"--- 系统诊断 ---\n{diag_text}"
        )

    if failed_reads:
        failed_text = "\n".join(_failed_diags)
        print(f"[警告] {len(failed_reads)}/{len(paths)} 个模板文件读取失败: {', '.join(failed_reads)}")
        for line in _failed_diags:
            print(f"       {line}")

    return templates


_template_skip_logged = False


def best_match_score(
    frame_processed: np.ndarray,
    templates: List[Template],
    scale: float = 1.0,
) -> Tuple[float, str, Tuple[int, int], List[Tuple[str, float]]]:
    global _template_skip_logged
    best_score = -1.0
    best_name = ""
    best_loc = (0, 0)
    all_scores = []
    fh, fw = frame_processed.shape[:2]
    skipped = 0

    for tpl in templates:
        tpl_img = tpl.image
        if abs(scale - 1.0) > 0.01:
            new_w = max(1, int(tpl_img.shape[1] * scale))
            new_h = max(1, int(tpl_img.shape[0] * scale))
            tpl_img = cv2.resize(tpl_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        th, tw = tpl_img.shape[:2]
        if th > fh or tw > fw:
            skipped += 1
            continue
        result = cv2.matchTemplate(frame_processed, tpl_img, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

        current_score = float(max_val)
        all_scores.append((tpl.name, current_score))

        if current_score > best_score:
            best_score = current_score
            best_name = tpl.name
            best_loc = (max_loc[0] + tw // 2, max_loc[1] + th // 2)

    if skipped == len(templates) and len(templates) > 0 and not _template_skip_logged:
        print(f"[诊断] 所有模板 ({len(templates)} 个) 尺寸均大于捕获帧 ({fw}x{fh})，匹配已跳过")
        _template_skip_logged = True

    return best_score, best_name, best_loc, all_scores


_match_single_missing_logged: set[str] = set()


def match_single(
    frame_processed: np.ndarray,
    templates: List[Template],
    target_name: str,
    scale: float = 1.0,
) -> float:
    target_key = normalize_template_name(target_name)
    fh, fw = frame_processed.shape[:2]

    for tpl in templates:
        if normalize_template_name(tpl.name) != target_key:
            continue
        tpl_img = tpl.image
        if abs(scale - 1.0) > 0.01:
            new_w = max(1, int(tpl_img.shape[1] * scale))
            new_h = max(1, int(tpl_img.shape[0] * scale))
            tpl_img = cv2.resize(tpl_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        th, tw = tpl_img.shape[:2]
        if th > fh or tw > fw:
            continue
        result = cv2.matchTemplate(frame_processed, tpl_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return float(max_val)

    if target_key not in _match_single_missing_logged:
        print(f"[诊断] 模板列表中未找到目标模板: {target_name}")
        _match_single_missing_logged.add(target_key)
    return 0.0


_yes_template_missing_logged = False


def best_yes_score_and_loc(
    frame_bgr: np.ndarray,
    templates: List[Template],
    scale: float,
) -> Tuple[float, Tuple[int, int]]:
    global _yes_template_missing_logged
    frame_edge = preprocess(frame_bgr)
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    fh, fw = frame_gray.shape[:2]

    best_score = -1.0
    best_loc = (0, 0)
    found = False

    for tpl in templates:
        if "yes" not in tpl.name.lower():
            continue
        found = True
        t_img = tpl.image
        if abs(scale - 1.0) > 0.01:
            t_img = cv2.resize(
                t_img,
                (max(1, int(t_img.shape[1] * scale)), max(1, int(t_img.shape[0] * scale))),
                interpolation=cv2.INTER_AREA,
            )

        th, tw = t_img.shape[:2]
        if th > fh or tw > fw:
            continue

        res_edge = cv2.matchTemplate(frame_edge, t_img, cv2.TM_CCOEFF_NORMED)
        res_gray = cv2.matchTemplate(frame_gray, t_img, cv2.TM_CCOEFF_NORMED)
        _, max_v_edge, _, max_l_edge = cv2.minMaxLoc(res_edge)
        _, max_v_gray, _, max_l_gray = cv2.minMaxLoc(res_gray)

        cur_v, cur_l = (max_v_edge, max_l_edge) if max_v_edge > max_v_gray else (max_v_gray, max_l_gray)
        if cur_v > best_score:
            best_score = float(cur_v)
            best_loc = (cur_l[0] + tw // 2, cur_l[1] + th // 2)

    if not found and not _yes_template_missing_logged:
        print(f"[诊断] 模板列表中未找到 'yes' 确认按钮模板，逃跑功能将无法定位点击坐标")
        _yes_template_missing_logged = True

    return best_score, best_loc
