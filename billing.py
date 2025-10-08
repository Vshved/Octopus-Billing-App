# billing.py
"""Логіка розрахунків та біллінгу"""

import math
from typing import Dict, List
from config import AppConfig

def ceil_to_step(minutes: int) -> int:
    """Округлення хвилин до заданого кроку вгору"""

    full_hours= minutes//60
    rest = minutes - full_hours*60
    if rest>=AppConfig.hour_step:
        full_hours = full_hours + 1

    return full_hours


def hourly_sum(duration_hours: int, weekday: str, people: int,
               tariffs: Dict[str, Dict[str, List[int]]],
               session_type: str = "table") -> int:
    """
    Розрахунок суми за погодинними тарифами

    Args:
        duration_hours Тривалість у годинах
        weekday: День тижня (українською)
        people: Кількість людей
        tariffs: Словник тарифів
        session_type: Тип місця ('table' або 'ps5')

    Returns:
        Сума до сплати
    """
    from constants import UA_WEEKDAYS

    if session_type not in tariffs:
        session_type = "table"

    # Визначаємо кількість годин

    #k = ceil_to_step(duration_minutes)



    # Отримуємо ціни для цього дня тижня
    prices = tariffs[session_type].get(
        weekday,
        tariffs[session_type][UA_WEEKDAYS[0]]
    )[:duration_hours]

    # Розраховуємо загальну суму
    total = int(sum(prices) * max(1, people))
    return total