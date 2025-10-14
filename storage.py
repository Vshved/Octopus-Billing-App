# storage.py
"""Робота з файлами - збереження та завантаження сесій"""

import json
import csv
from typing import Dict
from datetime import datetime
from pathlib import Path

from constants import SESSIONS_PATH, BILLS_CSV
from models import Session, Batch


def save_active_sessions(sessions: Dict[int, Session], counter: int):
    """Зберігає активні сесії в JSON"""
    print(f"\n💾 Зберігаю {len(sessions)} активних столів...")

    data = {
        "counter": counter,
        "sessions": []
    }

    for s in sessions.values():
        try:
            session_data = {
                "sid": s.sid,
                "name": s.name,
                "discount_pct": s.discount_pct,
                "place_type": s.place_type,
                "comment": s.comment,
                "batches": [
                    {"count": b.count, "start": b.start.isoformat(), "comment":b.comment}
                    for b in s.batches
                ]
            }
            data["sessions"].append(session_data)
            print(f"  ✓ Підготовлено стіл #{s.sid}: {s.name}")
        except Exception as e:
            print(f"  ❌ Помилка підготовки столу #{s.sid}: {e}")
            continue

    try:
        # Спочатку зберегти у тимчасовий файл
        temp_path = SESSIONS_PATH.with_suffix('.json.tmp')
        content = json.dumps(data, ensure_ascii=False, indent=2)
        temp_path.write_text(content, encoding="utf-8")

        # Якщо успішно - перейменувати
        if SESSIONS_PATH.exists():
            # Створити backup старого файлу
            backup_path = SESSIONS_PATH.with_suffix('.json.old')
            # ДОДАЙ ЦІ РЯДКИ - видали старий backup якщо існує
            if backup_path.exists():
                backup_path.unlink()  # Видаляємо старий .old файл
            SESSIONS_PATH.rename(backup_path)

        temp_path.rename(SESSIONS_PATH)
        print(f"✓ Файл збережено: {SESSIONS_PATH}")
        print(f"   Розмір: {len(content)} символів\n")

    except Exception as e:
        print(f"❌ Помилка збереження файлу: {e}")
        raise


def load_active_sessions() -> tuple[Dict[int, Session], int]:
    """Завантажує активні сесії з JSON"""
    if not SESSIONS_PATH.exists():
        print("ℹ️  Файл active_sessions.json не знайдено")
        return {}, 0

    try:
        content = SESSIONS_PATH.read_text(encoding="utf-8")
        print(f"📖 Читаю файл: {SESSIONS_PATH}")
        print(f"   Розмір файлу: {len(content)} символів")

        data = json.loads(content)
        sessions = {}

        for s_data in data.get("sessions", []):
            try:
                batches = [
                    Batch(
                        count=b["count"],
                        comment=b["comment"],
                        start=datetime.fromisoformat(b["start"]
                         )
                    )
                    for b in s_data.get("batches", [])
                ]

                s = Session(
                    sid=s_data["sid"],
                    name=s_data["name"],
                    batches=batches,
                    discount_pct=s_data.get("discount_pct", 0),
                    place_type=s_data.get("place_type", "table"),
                    comment = s_data.get("comment", "")
                )

                sessions[s.sid] = s
                print(f"  ✓ Завантажено стіл #{s.sid}: {s.name}, {s.total_people()} осіб")

            except Exception as e:
                print(f"  ❌ Помилка завантаження столу: {e}")
                continue

        counter = data.get("counter", 0)
        print(f"✓ Завантажено {len(sessions)} столів, counter={counter}\n")
        return sessions, counter

    except json.JSONDecodeError as e:
        print(f"❌ Помилка парсингу JSON: {e}")
        # Створити резервну копію пошкодженого файлу
        backup_path = SESSIONS_PATH.with_suffix('.json.backup')
        SESSIONS_PATH.rename(backup_path)
        print(f"   Пошкоджений файл збережено як: {backup_path}")
        return {}, 0
    except Exception as e:
        print(f"❌ Невідома помилка завантаження: {e}")
        return {}, 0


def save_closed_session(sid: int, name: str, people: int,
                        amount: int, mode: str, place_type: str):
    """Зберігає закриту сесію в CSV"""
    newfile = not BILLS_CSV.exists()
    with BILLS_CSV.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if newfile:
            writer.writerow([
                "id", "name", "people", "when",
                "amount_final", "mode", "place_type"
            ])
        writer.writerow([
            sid, name, people,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            amount, mode, place_type
        ])