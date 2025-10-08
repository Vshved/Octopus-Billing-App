# config.py
"""Конфігурація програми"""

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class AppConfig:
    """Налаштування програми"""

    # Інтерфейс
    window_width: int = 1000
    window_height: int = 640
    font_size: int = 13
    update_interval_ms: int = 1000  # Інтервал оновлення UI

    # Розрахунки
    #default_round_step: int = 60  # Округлення часу (хвилини)
    default_global_discount: int = 0  # Глобальна знижка (%)
    hour_step: int = 15

    # Тарифи
    max_hours: int = 8  # Максимальна кількість годин в тарифі

    # Файли
    tariffs_file: str = "tariffs.json"
    sessions_file: str = "active_sessions.json"
    bills_file: str = "closed_sessions.csv"
    config_file: str = "app_config.json"

    # Обмеження
    max_people_per_batch: int = 50
    max_discount: int = 100
    min_discount: int = 0

    # Резервне копіювання
    auto_backup: bool = True
    backup_interval_hours: int = 24
    max_backups: int = 7

    def save(self, path: Path | None = None):
        """Зберегти конфігурацію"""
        if path is None:
            path = Path(self.config_file)

        data = {
            'window_width': self.window_width,
            'window_height': self.window_height,
            'font_size': self.font_size,
            'update_interval_ms': self.update_interval_ms,
            'default_round_step': self.default_round_step,
            'default_global_discount': self.default_global_discount,
            'max_hours': self.max_hours,
            'tariffs_file': self.tariffs_file,
            'sessions_file': self.sessions_file,
            'bills_file': self.bills_file,
            'max_people_per_batch': self.max_people_per_batch,
            'max_discount': self.max_discount,
            'min_discount': self.min_discount,
            'auto_backup': self.auto_backup,
            'backup_interval_hours': self.backup_interval_hours,
            'max_backups': self.max_backups,
        }

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    @classmethod
    def load(cls, path: Path | None = None) -> 'AppConfig':
        """Завантажити конфігурацію"""
        config = cls()

        if path is None:
            path = Path(config.config_file)

        if not path.exists():
            return config

        try:
            data = json.loads(path.read_text(encoding='utf-8'))

            # Оновити значення з файлу
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            return config
        except Exception:
            # Якщо помилка - повернути налаштування за замовчуванням
            return config


# Глобальний екземпляр конфігурації
config = AppConfig.load()


# Функції для зручного доступу
def get_config() -> AppConfig:
    """Отримати поточну конфігурацію"""
    return config


def save_config():
    """Зберегти поточну конфігурацію"""
    config.save()


def reset_config():
    """Скинути до налаштувань за замовчуванням"""
    global config
    config = AppConfig()
    config.save()