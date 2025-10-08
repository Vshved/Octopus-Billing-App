# main.py
"""Точка входу в програму"""

import sys
from PyQt6 import QtWidgets

from main_window import ClubBillingApp
from styles import apply_global_style


def main():
    """Головна функція запуску програми"""
    app = QtWidgets.QApplication(sys.argv)

    # КРИТИЧНО для macOS: використовуємо Fusion замість нативного стилю
    app.setStyle("Fusion")

    apply_global_style(app)

    # Збільшений шрифт для кращої читабельності
    f = app.font()
    f.setPointSize(10)
    app.setFont(f)

    w = ClubBillingApp()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()