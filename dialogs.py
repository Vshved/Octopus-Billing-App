# dialogs.py
"""Діалогові вікна"""

from typing import Dict, List
from datetime import datetime

from PyQt6 import QtCore, QtWidgets, QtGui

from models import Session, Batch
from billing import ceil_to_step, hourly_sum
from storage import save_closed_session
from utils import create_choice_button


class EditSessionDialog(QtWidgets.QDialog):
    """Діалог редагування сесії"""

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редагування сесії")
        self.resize(800, 600)  # Встановлюємо розмір вікна
        self.setMinimumSize(700, 500)  # Мінімальний розмір
        self.session = session
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(15)  # Відступи між елементами

        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit(session.name)
        self.name_edit.setMinimumHeight(35)

        self.disc_spin = QtWidgets.QSpinBox()
        self.disc_spin.setRange(0, 100)
        self.disc_spin.setValue(session.discount_pct)
        self.disc_spin.setMinimumHeight(35)

        # Вибір типу місця
        default_idx = 1 if session.place_type == 'ps5' else 0
        self.type_btn, self.get_type_index = create_choice_button(
            ["Звичайний стіл", "PlayStation5"],
            default_idx
        )
        self.type_btn.setMinimumHeight(35)
        # Додаємо поле для коментаря сесії
        self.comment_edit = QtWidgets.QTextEdit()
        self.comment_edit.setPlaceholderText("Коментар...")
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlainText(session.comment)

        form.addRow("Ім'я:", self.name_edit)
        #form.addRow("Знижка столу, %:", self.disc_spin)
        form.addRow("Тип місця:", self.type_btn)
        form.addRow("Коментар:", self.comment_edit)
        lay.addLayout(form)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["К-сть", "Старт (HH:MM)", "Коментар"])

        # Налаштування розмірів колонок
        self.table.setColumnWidth(0, 180)  # Колонка кількості - збільшено
        self.table.setColumnWidth(1, 220)  # Колонка часу - збільшено
        self.table.setColumnWidth(2, 180)  # Колонка кнопки видалення

        # Висота рядків за замовчуванням
        self.table.verticalHeader().setDefaultSectionSize(60)

        # Вимкнути растягування останньої колонки
        self.table.horizontalHeader().setStretchLastSection(False)

        # Стилі таблиці
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 10px;
            }
        """)

        lay.addWidget(self.table)

        btns = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("+ Додати пакет")
        self.btn_add.setMinimumHeight(35)
        btns.addWidget(self.btn_add)
        btns.addStretch(1)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        # Збільшити кнопки Save/Cancel
        for button in btn_box.buttons():
            button.setMinimumHeight(35)
            button.setMinimumWidth(100)
        btns.addWidget(btn_box)
        lay.addLayout(btns)

        self.btn_add.clicked.connect(self.add_row)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        self.load_rows()

    def load_rows(self):
        """Завантаження пакетів у таблицю"""
        self.table.setRowCount(0)
        for b in self.session.batches:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Встановити висоту рядка
            self.table.setRowHeight(r, 60)

            # SpinBox для кількості
            sp = QtWidgets.QSpinBox()
            sp.setRange(1, 50)
            sp.setValue(b.count)
            sp.setMinimumHeight(50)
            sp.setFixedHeight(50)
            sp.setStyleSheet("""
                QSpinBox {
                    font-size: 16px;
                    padding: 8px;
                }
            """)

            # TimeEdit для часу
            tm = QtWidgets.QTimeEdit()
            tm.setDisplayFormat("HH:mm")
            tm.setTime(QtCore.QTime(b.start.hour, b.start.minute))
            tm.setMinimumHeight(50)
            tm.setFixedHeight(50)
            tm.setStyleSheet("""
                QTimeEdit {
                    font-size: 16px;
                    padding: 2px;
                }
            """)
            comment = QtWidgets.QLineEdit(b.comment)
            comment.setPlaceholderText("Коментар...")
            # Кнопка видалення
            rm = QtWidgets.QPushButton("Видалити")
            rm.setMinimumHeight(50)
            rm.setFixedHeight(50)
            rm.setStyleSheet("""
                QPushButton {
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    padding: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #dc2626;
                }
            """)
            rm.clicked.connect(lambda _=None, row=r: self.remove_row(row))

            self.table.setCellWidget(r, 0, sp)
            self.table.setCellWidget(r, 1, tm)
            self.table.setCellWidget(r, 2, comment)
            self.table.setCellWidget(r, 3, rm)

    def add_row(self):
        """Додавання нового пакету"""
        r = self.table.rowCount()
        self.table.insertRow(r)

        # Встановити висоту рядка
        self.table.setRowHeight(r, 60)

        # SpinBox для кількості
        sp = QtWidgets.QSpinBox()
        sp.setRange(1, 50)
        sp.setValue(1)
        sp.setMinimumHeight(50)
        sp.setFixedHeight(50)
        sp.setStyleSheet("""
            QSpinBox {
                font-size: 16px;
                padding: 8px;
            }
        """)

        # TimeEdit для часу
        tm = QtWidgets.QTimeEdit()
        tm.setDisplayFormat("HH:mm")
        tm.setTime(QtCore.QTime.currentTime())
        tm.setMinimumHeight(50)
        tm.setFixedHeight(50)
        tm.setStyleSheet("""
            QTimeEdit {
                font-size: 16px;
                padding: 8px;
            }
        """)
        comment = QtWidgets.QLineEdit()
        comment.setPlaceholderText("Коментар...")
        # Кнопка видалення
        rm = QtWidgets.QPushButton("Видалити")
        rm.setMinimumHeight(50)
        rm.setFixedHeight(50)
        rm.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        rm.clicked.connect(lambda _=None, row=r: self.remove_row(row))

        self.table.setCellWidget(r, 0, sp)
        self.table.setCellWidget(r, 1, tm)
        self.table.setCellWidget(r, 2, comment)
        self.table.setCellWidget(r, 3, rm)

    def remove_row(self, row: int):
        """Видалення пакету"""
        reply = QtWidgets.QMessageBox.question(
            self, "Підтвердження",
            "Видалити цей пакет?",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.table.removeRow(row)

    def apply_changes(self):
        """Застосування змін до сесії"""
        self.session.name = self.name_edit.text().strip() or self.session.name
        self.session.discount_pct = self.disc_spin.value()
        self.session.place_type = 'ps5' if self.get_type_index() == 1 else 'table'
        self.session.comment = self.comment_edit.toPlainText().strip()
        new_batches: List[Batch] = []
        today = datetime.now().date()
        now = datetime.now()

        for r in range(self.table.rowCount()):
            sp: QtWidgets.QSpinBox = self.table.cellWidget(r, 0)  # type: ignore
            tm: QtWidgets.QTimeEdit = self.table.cellWidget(r, 1)  # type: ignore
            comment_widget: QtWidgets.QLineEdit = self.table.cellWidget(r, 2)  # type: ignore
            if not sp or not tm:
                continue
            cnt = sp.value()
            qtime = tm.time()
            dt = datetime(today.year, today.month, today.day,
                          qtime.hour(), qtime.minute())
            batch_comment = comment_widget.text().strip() if comment_widget else ""
            # Перевірка: час не може бути в майбутньому
            if dt > now:
                QtWidgets.QMessageBox.warning(
                    self, "Помилка",
                    f"Час старту пакету #{r + 1} ({qtime.toString('HH:mm')}) "
                    f"не може бути в майбутньому!"
                )
                return False

            new_batches.append(Batch(count=cnt, start=dt, comment=batch_comment))

        if not new_batches:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Додайте хоча б один пакет!"
            )
            return False

        new_batches.sort(key=lambda b: b.start)
        self.session.batches = new_batches
        return True

    def accept(self):
        if self.apply_changes():
            super().accept()


class PartialBillDialog(QtWidgets.QDialog):
    """Діалог часткового розрахунку"""

    def __init__(self, session: Session, weekday: str,
                 tariffs: Dict[str, Dict[str, List[int]]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Частковий розрахунок")
        self.resize(850, 600)  # Встановлюємо розмір
        self.setMinimumSize(800, 500)  # Мінімальний розмір
        self.session = session
        self.weekday = weekday
        from config import AppConfig
        self.round_step = AppConfig.hour_step
        self.tariffs = tariffs

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(15)
        # === ІНФОРМАЦІЯ ПРО СЕСІЮ ===
        info_group = QtWidgets.QGroupBox("Інформація про стіл")
        info_layout = QtWidgets.QFormLayout()

        info_layout.addRow("Ім'я:", QtWidgets.QLabel(f"<b>{session.name}</b>"))
        info_layout.addRow("ID столу:", QtWidgets.QLabel(str(session.sid)))

        place_type = "PlayStation 5 🎮" if session.place_type == 'ps5' else "Звичайний стіл"
        info_layout.addRow("Тип місця:", QtWidgets.QLabel(place_type))

        total_people = session.total_people()
        info_layout.addRow("Всього людей:", QtWidgets.QLabel(f"<b>{total_people}</b>"))


        # Коментар сесії
        if session.comment:
            comment_widget = QtWidgets.QTextEdit()
            comment_widget.setPlainText(session.comment)
            comment_widget.setReadOnly(True)
            comment_widget.setMaximumHeight(60)
            comment_widget.setStyleSheet(
                "background: #fef3c7; border: 1px solid #fbbf24; border-radius: 4px; padding: 5px;")
            info_layout.addRow("💬 Коментар:", comment_widget)

        info_group.setLayout(info_layout)
        lay.addWidget(info_group)
        #if session.comment:
         #   comment_label = QtWidgets.QLabel(f"💬 Коментар: {session.comment}")
         #   comment_label.setStyleSheet("background: #fef3c7; padding: 10px; border-radius: 5px; color: #92400e;")
        #    comment_label.setWordWrap(True)
        #    lay.addWidget(comment_label)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Пакет", "К-сть", "Оплатити зараз", "Час початку", "Годин нараховано", "Сума", "Коментар"
        ])

        # Налаштування розмірів колонок
        self.table.setColumnWidth(0, 50)  # Пакет
        self.table.setColumnWidth(1, 100)  # К-сть у пак.
        self.table.setColumnWidth(2, 100)  # Оплатити зараз
        self.table.setColumnWidth(3, 120)  # Час початку
        self.table.setColumnWidth(4, 120)  # Годин нараховано
        self.table.setColumnWidth(5, 100)  # Сума
        self.table.setColumnWidth(6, 130)  # Коментар

        # Висота рядків
        self.table.verticalHeader().setDefaultSectionSize(30)

        self.table.horizontalHeader().setStretchLastSection(True)

        # Стилі таблиці
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                gridline-color: #e5e7eb;
                border: 1px solid #e5e7eb;
            }
            QTableWidget::item {
                padding: 2px;
            }
        """)

        lay.addWidget(self.table)

        self.lbl_total = QtWidgets.QLabel("Сума до сплати: 0")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")

        btns = QtWidgets.QHBoxLayout()
        #btn_recalc = QtWidgets.QPushButton("Розрахувати")
        #btn_recalc.setMinimumHeight(40)
        #btn_recalc.setMinimumWidth(120)

        btn_ok = QtWidgets.QPushButton("Оплатити")
        btn_ok.setObjectName("primary")
        btn_ok.setMinimumHeight(40)
        btn_ok.setMinimumWidth(120)

        btn_cancel = QtWidgets.QPushButton("Скасувати")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setMinimumWidth(120)

        btns.addWidget(self.lbl_total)
        btns.addStretch(1)
        #btns.addWidget(btn_recalc)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        lay.addLayout(btns)

        #btn_recalc.clicked.connect(self.recalc)
        btn_ok.clicked.connect(self.do_save)
        btn_cancel.clicked.connect(self.reject)
        self.pay_spinboxes = []
        self.load_rows()
        self.recalc()  # Автоматично розрахувати при відкритті


    def load_rows(self):
        """Завантаження пакетів для розрахунку"""
        self.table.setRowCount(0)
        for i, b in enumerate(self.session.batches, 1):
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Встановити висоту рядка
            self.table.setRowHeight(r, 60)

            # Номер пакету
            item_num = QtWidgets.QTableWidgetItem(f"{i}")
            item_num.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item_num.setFlags(item_num.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)  # ADD THIS
            font = item_num.font()
            font.setPointSize(14)
            item_num.setFont(font)
            self.table.setItem(r, 0, item_num)

            # Кількість у пакеті
            item_count = QtWidgets.QTableWidgetItem(str(b.count))
            item_count.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item_count.setFlags(item_count.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item_count.setFont(font)
            self.table.setItem(r, 1, item_count)

            # SpinBox для оплати
            pay = QtWidgets.QSpinBox()
            pay.setRange(0, b.count)
            pay.setValue(0)  # За замовчуванням 0
            pay.setMinimumHeight(30)
            pay.setFixedHeight(30)
            pay.setStyleSheet("""
                QSpinBox {
                    font-size: 16px;
                    padding: 8px;
                }
            """)
            pay.valueChanged.connect(self.recalc)
            self.pay_spinboxes.append(pay)  # ADD THIS - store reference

            # CREATE CONTAINER TO CENTER THE SPINBOX
            container = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(container)
            layout.addWidget(pay)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)  # Center vertically
            layout.setContentsMargins(0, 0, 0, 0)  # Remove extra padding

            self.table.setCellWidget(r, 2, container)  # Use container instead of pay directly

            # Час старту
            item_start = QtWidgets.QTableWidgetItem(b.start.strftime("%H:%M"))
            item_start.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item_start.setFlags(item_start.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item_start.setFlags(item_start.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item_start.setFont(font)
            self.table.setItem(r, 3, item_start)

            # Годин нараховано
            minutes = int((datetime.now() - b.start).total_seconds() // 60)
            hours = ceil_to_step(minutes)
            item_hours = QtWidgets.QTableWidgetItem(str(hours))
            item_hours.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item_hours.setFlags(item_hours.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item_hours.setFont(font)
            self.table.setItem(r, 4, item_hours)

            # Сума
            item_sum = QtWidgets.QTableWidgetItem()
            item_sum.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item_sum.setFlags(item_sum.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item_sum.setFont(font)
            self.table.setItem(r, 5, item_sum)

            # Показуємо коментар батчу
            comment_item = QtWidgets.QTableWidgetItem(b.comment if b.comment else "—")
            comment_item.setFlags(comment_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            if b.comment:
                comment_item.setForeground(QtGui.QColor("#059669"))
            self.table.setItem(r, 6, comment_item)

    def recalc(self):
        """Перерахунок суми"""
        total = 0
        for r, b in enumerate(self.session.batches):
            #sp: QtWidgets.QSpinBox = self.table.cellWidget(r, 2)  # type: ignore
            #pay_now = sp.value() if sp else 0
            pay_now = self.pay_spinboxes[r].value()  # USE STORED REFERENCE
            if pay_now > 0:
                minutes = int((datetime.now() - b.start).total_seconds() // 60)
                hours = ceil_to_step(minutes)
                amount = hourly_sum(
                    hours, self.weekday, pay_now,
                    self.tariffs, session_type=self.session.place_type
                )
                total += amount
                item = self.table.item(r, 5)
                if item:
                    item.setText(f"{amount} грн")

            else:
                item = self.table.item(r, 5)
                if item:
                    item.setText("—")

        """disc = self.session.discount_pct
        if disc:
            orig_total = total
            total = int(round(total * (100 - disc) / 100.0))
            self.lbl_total.setText(
                f"Сума до сплати: {total} грн "
                f"(було {orig_total} грн, знижка {disc}%)"
            )
        else:"""
        self.lbl_total.setText(f"Сума до сплати: {total} грн")
        return total

    def do_save(self):
        """Збереження оплати"""
        total = self.recalc()

        # Підтвердження оплати
        reply = QtWidgets.QMessageBox.question(
            self, "Підтвердження оплати",
            f"Провести оплату на суму {total} грн?",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        for r, b in enumerate(list(self.session.batches)):
            sp: QtWidgets.QSpinBox = self.table.cellWidget(r, 2)  # type: ignore
            pay_now = sp.value() if sp else 0
            if pay_now > 0:
                b.count -= pay_now
                if b.count <= 0:
                    self.session.batches.remove(b)

        save_closed_session(
            self.session.sid, self.session.name, 0,
            total, "partial", self.session.place_type
        )

        QtWidgets.QMessageBox.information(
            self, "Успішно",
            f"Оплату на суму {total} грн проведено"
        )
        self.accept()


class FullBillDialog(QtWidgets.QDialog):
    """Діалог повного розрахунку з усією інформацією"""

    def __init__(self, session: Session, weekday: str, round_step: int, tariffs: Dict[str, Dict[str, List[int]]],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Повний розрахунок - {session.name}")
        self.session = session
        self.weekday = weekday
        self.round_step = round_step
        self.tariffs = tariffs

        lay = QtWidgets.QVBoxLayout(self)

        # === ІНФОРМАЦІЯ ПРО СЕСІЮ ===
        info_group = QtWidgets.QGroupBox("Інформація про стіл")
        info_layout = QtWidgets.QFormLayout()

        info_layout.addRow("Ім'я:", QtWidgets.QLabel(f"<b>{session.name}</b>"))
        info_layout.addRow("ID столу:", QtWidgets.QLabel(str(session.sid)))

        place_type = "PlayStation 5 🎮" if session.place_type == 'ps5' else "Звичайний стіл"
        info_layout.addRow("Тип місця:", QtWidgets.QLabel(place_type))

        total_people = session.total_people()
        info_layout.addRow("Всього людей:", QtWidgets.QLabel(f"<b>{total_people}</b>"))

        #if session.discount_pct > 0:
        #    discount_label = QtWidgets.QLabel(f"<b style='color: #2563eb;'>{session.discount_pct}%</b>")
        #    info_layout.addRow("Знижка столу:", discount_label)

        # Коментар сесії
        if session.comment:
            comment_widget = QtWidgets.QTextEdit()
            comment_widget.setPlainText(session.comment)
            comment_widget.setReadOnly(True)
            comment_widget.setMaximumHeight(60)
            comment_widget.setStyleSheet(
                "background: #fef3c7; border: 1px solid #fbbf24; border-radius: 4px; padding: 5px;")
            info_layout.addRow("💬 Коментар:", comment_widget)

        info_group.setLayout(info_layout)
        lay.addWidget(info_group)

        # === ТАБЛИЦЯ БАТЧІВ ===
        batch_group = QtWidgets.QGroupBox("Деталі по пакетах")
        batch_layout = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Пакет", "Кількість", "Час початку", "Годин до сплати", "Коментар", "Сума"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        batch_layout.addWidget(self.table)

        batch_group.setLayout(batch_layout)
        lay.addWidget(batch_group)

        # === ПІДСУМОК ===
        summary_group = QtWidgets.QGroupBox("Підсумок")
        summary_layout = QtWidgets.QVBoxLayout()

        #self.lbl_subtotal = QtWidgets.QLabel()
        #self.lbl_discount = QtWidgets.QLabel()
        self.lbl_total = QtWidgets.QLabel()
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669;")

        #summary_layout.addWidget(self.lbl_subtotal)
        #summary_layout.addWidget(self.lbl_discount)
        summary_layout.addWidget(self.lbl_total)

        summary_group.setLayout(summary_layout)
        lay.addWidget(summary_group)

        # === КНОПКИ ===
        btns = QtWidgets.QHBoxLayout()
        btn_close_table = QtWidgets.QPushButton("Розрахувати і Закрити стіл")
        btn_close_table.setObjectName("danger")
        btn_close_table.setMinimumHeight(40)
        btn_cancel = QtWidgets.QPushButton("Скасувати")
        btn_cancel.setMinimumHeight(40)

        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_close_table)
        lay.addLayout(btns)

        btn_close_table.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        # Завантажуємо дані
        self.load_data()
        self.resize(700, 600)
        self.pay_spinboxes = []  # ADD THIS LINE

    def load_data(self):
        """Завантажує всі дані про сесію"""
        self.table.setRowCount(0)
        subtotal = 0

        for i, b in enumerate(self.session.batches, 1):
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Номер пакету
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(f"#{i}"))

            # Кількість людей
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(str(b.count)))

            # Час старту
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(b.start.strftime("%H:%M")))

            # Тривалість
            minutes = int((datetime.now() - b.start).total_seconds() // 60)
            hours = ceil_to_step(minutes)

            duration_text = f"{hours} год"
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(duration_text))

            # Коментар
            comment_item = QtWidgets.QTableWidgetItem(b.comment if b.comment else "—")
            if b.comment:
                comment_item.setForeground(QtGui.QColor("#059669"))
            self.table.setItem(r, 4, comment_item)

            # Сума за пакет
            amount = hourly_sum(hours*60, self.weekday, b.count, self.tariffs,
                                session_type=self.session.place_type)
            subtotal += amount
            self.table.setItem(r, 5, QtWidgets.QTableWidgetItem(f"{amount} грн"))

        # Розрахунок підсумку
        #disc = self.session.discount_pct
        total = subtotal

        #self.lbl_subtotal.setText(f"Сума без знижки: {subtotal} грн")

        #if disc > 0:
        #    discount_amount = int(subtotal * disc / 100)
        #    total = subtotal - discount_amount
        #    self.lbl_discount.setText(f"Знижка ({disc}%): -{discount_amount} грн")
        #    self.lbl_discount.setStyleSheet("color: #2563eb;")
        #else:
        #    self.lbl_discount.setText("Знижка: немає")
        #    self.lbl_discount.setStyleSheet("color: #6b7280;")

        self.lbl_total.setText(f"РАЗОМ ДО СПЛАТИ: {total} грн")