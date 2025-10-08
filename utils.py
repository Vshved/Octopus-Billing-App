# utils.py
"""Допоміжні функції"""

from typing import Callable, Tuple, List
from PyQt6 import QtWidgets


def create_choice_button(items: List[str], default_index: int = 0) -> Tuple[QtWidgets.QPushButton, Callable]:
    """
    Створює кнопку-селектор замість ComboBox

    Args:
        items: Список варіантів вибору
        default_index: Індекс обраного за замовчуванням

    Returns:
        Tuple з кнопкою та функцією для отримання поточного індексу
    """
    current_index = [default_index]  # Використовуємо список для мутабельності

    btn = QtWidgets.QPushButton(items[default_index])
    btn.setStyleSheet("""
        QPushButton {
            text-align: left;
            padding-left: 10px;
            padding-right: 25px;
        }
    """)

    menu = QtWidgets.QMenu()
    actions = []

    def update_button(index: int):
        current_index[0] = index
        btn.setText(items[index])

    for i, item in enumerate(items):
        action = menu.addAction(item)
        action.triggered.connect(lambda checked=False, idx=i: update_button(idx))
        actions.append(action)

    btn.setMenu(menu)

    # Функція для отримання поточного індексу
    def get_current_index():
        return current_index[0]

    return btn, get_current_index