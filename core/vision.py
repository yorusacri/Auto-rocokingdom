import glob
import os
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


def load_templates() -> List[Template]:
    pattern = os.path.join(CONFIG.template_dir, CONFIG.template_pattern)
    paths = sorted(glob.glob(pattern))
    templates: List[Template] = []

    for path in paths:
        raw = cv2.imread(path)
        if raw is None:
            continue
        if "yes" in path.lower():
            processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        else:
            processed = preprocess(raw)

        if "qiudaidai" in path.lower():
            processed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

        templates.append(Template(name=os.path.basename(path), image=processed))

    if not templates:
        raise FileNotFoundError(
            "No template images found. Put PNG files into templates/ first."
        )

    return templates


def best_match_score(
    frame_processed: np.ndarray,
    templates: List[Template],
    scale: float = 1.0,
) -> Tuple[float, str, Tuple[int, int], List[Tuple[str, float]]]:
    best_score = -1.0
    best_name = ""
    best_loc = (0, 0)
    all_scores = []
    fh, fw = frame_processed.shape[:2]

    for tpl in templates:
        tpl_img = tpl.image
        if abs(scale - 1.0) > 0.01:
            new_w = max(1, int(tpl_img.shape[1] * scale))
            new_h = max(1, int(tpl_img.shape[0] * scale))
            tpl_img = cv2.resize(tpl_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        th, tw = tpl_img.shape[:2]
        if th > fh or tw > fw:
            continue
        result = cv2.matchTemplate(frame_processed, tpl_img, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

        current_score = float(max_val)
        all_scores.append((tpl.name, current_score))

        if current_score > best_score:
            best_score = current_score
            best_name = tpl.name
            best_loc = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
    return best_score, best_name, best_loc, all_scores


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
    return 0.0


def best_yes_score_and_loc(
    frame_bgr: np.ndarray,
    templates: List[Template],
    scale: float,
) -> Tuple[float, Tuple[int, int]]:
    frame_edge = preprocess(frame_bgr)
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    fh, fw = frame_gray.shape[:2]

    best_score = -1.0
    best_loc = (0, 0)

    for tpl in templates:
        if "yes" not in tpl.name.lower():
            continue
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

    return best_score, best_loc
