# constants.py
"""Константи проекту"""

from pathlib import Path

# Шляхи до файлів
TARIFFS_PATH = Path("tariffs.json")
BILLS_CSV = Path("closed_sessions.csv")
SESSIONS_PATH = Path("active_sessions.json")

# Дні тижня українською
UA_WEEKDAYS = [
    "понеділок", "вівторок", "середа", "четвер",
    "п'ятниця", "субота", "неділя"
]

# Мітки годин
HOUR_LABELS = [
    "1ша година", "2га година", "3тя година", "4та година",
    "5та година", "6та година", "7ма година", "8ма година"
]