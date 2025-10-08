# tariffs.py
"""Управління тарифами"""

import json
from typing import Dict, List
from constants import TARIFFS_PATH, UA_WEEKDAYS


def default_tariffs() -> Dict[str, Dict[str, List[int]]]:
    """Повертає тарифи за замовчуванням"""
    base_table = {
        "понеділок": [50, 50, 50, 30, 0, 0, 0, 0],
        "вівторок": [50, 50, 50, 30, 0, 0, 0, 0],
        "середа": [50, 50, 50, 30, 0, 0, 0, 0],
        "четвер": [50, 50, 50, 30, 0, 0, 0, 0],
        "п'ятниця": [65, 65, 65, 35, 0, 0, 0, 0],
        "субота": [65, 65, 65, 35, 0, 0, 0, 0],
        "неділя": [65, 65, 65, 35, 0, 0, 0, 0],
    }
    base_ps5 = {
        "понеділок": [50, 50, 50, 50, 50, 50, 50, 50],
        "вівторок": [50, 50, 50, 50, 50, 50, 50, 50],
        "середа": [50, 50, 50, 50, 50, 50, 50, 50],
        "четвер": [50, 50, 50, 50, 50, 50, 50, 50],
        "п'ятниця": [65, 65, 65, 65, 65, 65, 65, 65],
        "субота": [65, 65, 65, 65, 65, 65, 65, 65],
        "неділя": [65, 65, 65, 65, 65, 65, 65, 65],
    }
    return {"table": base_table, "ps5": base_ps5}


def load_tariffs() -> Dict[str, Dict[str, List[int]]]:
    """Завантаження тарифів з файлу"""
    if TARIFFS_PATH.exists():
        try:
            obj = json.loads(TARIFFS_PATH.read_text(encoding="utf-8"))
            res = {}
            for kind in ("table", "ps5"):
                part = obj.get(kind, default_tariffs()[kind])
                data = {
                    d: list(map(int, part.get(d, default_tariffs()[kind][d])))[:8]
                    for d in UA_WEEKDAYS
                }
                for d in data:
                    if len(data[d]) < 8:
                        data[d] += [data[d][-1]] * (8 - len(data[d]))
                res[kind] = data
            return res
        except Exception:
            pass
    return default_tariffs()


def save_tariffs(tariffs: Dict[str, Dict[str, List[int]]]):
    """Збереження тарифів у файл"""
    TARIFFS_PATH.write_text(
        json.dumps(tariffs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )