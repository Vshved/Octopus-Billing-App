# models.py
"""Моделі даних для сесій та пакетів"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class Batch:
    """Пакет людей, які прийшли в один час"""
    count: int
    start: datetime
    comment: str = ""  # Коментар для батчу


@dataclass
class Session:
    """Сесія (стіл) з клієнтами"""
    sid: int
    name: str
    batches: List[Batch] = field(default_factory=list)
    discount_pct: int = 0
    place_type: str = "table"  # 'table' or 'ps5'
    comment: str = ""  # Коментар для сесії

    def total_people(self) -> int:
        """Загальна кількість людей на столі"""
        return sum(b.count for b in self.batches)

    def minutes_for_batch(self, b: Batch) -> int:
        """Скільки хвилин пройшло для пакету"""
        return int((datetime.now() - b.start).total_seconds() // 60)

    def total_amount(self, weekday: str, round_step: int,
                     tariffs: Dict[str, Dict[str, List[int]]]) -> int:
        """Загальна сума для всіх людей на столі"""
        from billing import ceil_to_step, hourly_sum

        total = 0
        for b in self.batches:
            m = ceil_to_step(self.minutes_for_batch(b))

            total += hourly_sum(m, weekday, b.count, tariffs,
                                session_type=self.place_type)
           # import pdb;            pdb.set_trace()
        return total

    def settle_one(self, weekday: str, round_step: int,
                   tariffs: Dict[str, Dict[str, List[int]]]) -> int:
        """Розрахувати одну людину з останнього пакету"""
        from billing import ceil_to_step, hourly_sum

        if not self.batches:
            return 0
        b = self.batches[-1]
        m = ceil_to_step(self.minutes_for_batch(b))
        amount = hourly_sum(m, weekday, 1, tariffs,
                            session_type=self.place_type)
        b.count -= 1
        if b.count <= 0:
            self.batches.pop()
        return amount
    def get_hours(self):
        """
        Повертає (деталі_пакетів, total_hours).
        details list: для кожного пакету dict з полями
          - index: індекс пакету (0 - перший)
          - minutes: фактичні хвилини
          - rounded_minutes: хвилини після округлення до round_step
          - hours: rounded_minutes / 60 (float)
        total_hours: сума всіх rounded_minutes у годинах (float)
        """
        from billing import ceil_to_step


        total_hours = 0

        for i, b in enumerate(self.batches):
            minutes = self.minutes_for_batch(b)
            hours = ceil_to_step(minutes)
            total_hours += hours
        return total_hours