# main_window.py
"""Головне вікно програми"""

from typing import Dict
from datetime import datetime


from PyQt6 import QtCore, QtGui, QtWidgets

from constants import UA_WEEKDAYS, HOUR_LABELS
from config import AppConfig
from models import Session, Batch
from tariffs import load_tariffs, save_tariffs
from storage import (
    load_active_sessions, save_active_sessions, save_closed_session
)
from dialogs import EditSessionDialog, PartialBillDialog, FullBillDialog
from utils import create_choice_button


class AddPeopleDialog(QtWidgets.QDialog):
    """Діалог додавання людей з коментарем"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати людей до столу")

        lay = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()

        self.count_spin = QtWidgets.QSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(1)
        self.count_spin.setMinimumWidth(200)

        self.comment_edit = QtWidgets.QTextEdit()
        self.comment_edit.setPlaceholderText("Коментар...")
        self.comment_edit.setMaximumHeight(80)

        form.addRow("Кількість людей:", self.count_spin)
        form.addRow("Коментар:", self.comment_edit)

        lay.addLayout(form)

        # Кнопки
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        self.resize(400, 250)

    def get_count(self) -> int:
        return self.count_spin.value()

    def get_comment(self) -> str:
        return self.comment_edit.toPlainText().strip()

class ClubBillingApp(QtWidgets.QMainWindow):
    """Головне вікно касової системи"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OctopuS — Калькулятор оплат")
        self.resize(1200, 640)  # Збільшено ширину для нових колонок
        self.setMinimumSize(1100, 600)  # Мінімальна ширина

        self.tariffs: Dict = load_tariffs()
        self.sessions, self.counter = load_active_sessions()

        self.global_discount = 0
        self.round_step = 60
        self.last_selected_sid: int | None = None

        self._build_menu()
        self._build_central()

        # Статус-бар
        self.status_bar = self.statusBar()
        if self.sessions:
            self.status_bar.showMessage(
                f"✓ Завантажено {len(self.sessions)} активних столів"
            )
        else:
            self.status_bar.showMessage("Готово до роботи")

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_rows)
        self.timer.start(3000)

        # Таймер автозбереження (кожну хвилину)
        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start( 60 * 1000)  # 1 хвилина


    def _on_selection_changed(self):
        """Зберігає ID обраного столу"""
        s = self._selected_session()
        if s:
            self.last_selected_sid = s.sid
        else:
            self.last_selected_sid = None



    def _build_menu(self):
        """Побудова меню"""
        mb = self.menuBar()
        m_menu = mb.addMenu("Меню")
        m_daily = mb.addMenu("Звіти")
        m_help = mb.addMenu("Допомога")

        act_add = QtGui.QAction("Додати клієнта", self)
        act_add.setShortcut("Ctrl+N")
        act_add.triggered.connect(self.add_session_dialog)

        act_tariffs = QtGui.QAction("Тарифи", self)
        act_tariffs.setShortcut("Ctrl+T")
        act_tariffs.triggered.connect(self.open_tariffs)

        #act_settings = QtGui.QAction("Налаштування", self)
        #act_settings.setShortcut("Ctrl+,")
        #act_settings.triggered.connect(self.open_settings)

        act_save = QtGui.QAction("💾 Зберегти зараз", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.manual_save)

        act_daily_report = QtGui.QAction("📊 Денний звіт", self)
        act_daily_report.setShortcut("Ctrl+R")
        act_daily_report.triggered.connect(self.open_daily_report)
        m_daily.addAction(act_daily_report)

        m_menu.addAction(act_add)
        m_menu.addSeparator()
        m_menu.addAction(act_save)
        m_menu.addSeparator()
        m_menu.addAction(act_tariffs)
        m_menu.addSeparator()
        m_menu.addAction(act_daily_report)
        #m_menu.addAction(act_settings)

        act_shortcuts = QtGui.QAction("Клавіатурні скорочення", self)
        act_shortcuts.triggered.connect(self.show_shortcuts)
        m_help.addAction(act_shortcuts)

    def open_daily_report(self):
        """Відкрити денний звіт"""
        from dialogs import DailyReportDialog
        dlg = DailyReportDialog(self)
        dlg.exec()

    def _build_central(self):
        """Побудова центральної частини"""
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        lay = QtWidgets.QVBoxLayout(w)
        lay.setSpacing(8)
        lay.setContentsMargins(2, 2, 2, 2)

        # Верхня панель
        top_panel = QtWidgets.QHBoxLayout()
        self.lbl_active = QtWidgets.QLabel("Активних столів: 0")
        self.lbl_active.setStyleSheet("font-weight: bold; color: #2563eb;")
        self.lbl_people = QtWidgets.QLabel("Всього людей: 0")
        self.lbl_people.setStyleSheet("font-weight: bold; color: #059669;")
        top_panel.addWidget(self.lbl_active)
        top_panel.addWidget(self.lbl_people)
        top_panel.addStretch()
        lay.addLayout(top_panel)

        # Таблиця
        self.table = QtWidgets.QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Ім'я", "Кількість", "Час початку", "Годин до сплати", "Сума", "Коментар",
            "Додати", "Редагувати", "Часткова Оплата", "Повна оплата"])
        self.table.setShowGrid(False)  # Turn off thick gridlines
        self.table.setAlternatingRowColors(True)  # Use alternating rows instead

        # Налаштування ширини колонок
        self.table.setColumnWidth(0, 80)  # ID
        self.table.setColumnWidth(1, 150)  # Ім'я
        self.table.setColumnWidth(2, 60)  # К-сть
        self.table.setColumnWidth(3, 80)  # Час
        self.table.setColumnWidth(4, 110)  # Годин до сплати
        self.table.setColumnWidth(5, 80)  # Сума
        self.table.setColumnWidth(6, 150)  # Коментар
        self.table.setColumnWidth(7, 80)  # додати
        self.table.setColumnWidth(8, 80)  # Редагувати
        self.table.setColumnWidth(9, 120)  # Часткова оплата

        # Кнопки матимуть авто-ширину

        # Висота рядків
        self.table.verticalHeader().setDefaultSectionSize(60)  # Висота рядка 50px

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        #self.table.setShowGrid(True)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self.edit_selected_session)
        lay.addWidget(self.table)

        # Панель керування
        ctrl = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("+ Новий стіл")
        self.btn_add.setObjectName("primary")
        self.btn_add.clicked.connect(self.add_session_dialog)
        ctrl.addWidget(self.btn_add)
        lay.addLayout(ctrl)

    def add_session_dialog(self):
        """Діалог додавання нової сесії"""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Реєстрація відвідувача")
        dlg.setMinimumSize(450, 250)
        lay = QtWidgets.QVBoxLayout(dlg)

        f = QtWidgets.QFormLayout()

        name = QtWidgets.QLineEdit()
        name.setPlaceholderText("Введи ім'я клієнта")
        name.setMinimumHeight(35)

        ppl = QtWidgets.QSpinBox()
        ppl.setRange(1, 50)
        ppl.setValue(2)
        ppl.setMinimumHeight(35)

        type_btn, get_type_index = create_choice_button(
            ["Звичайний стіл", "PlayStation5"], 0
        )
        type_btn.setMinimumHeight(35)
        # Додаємо поле коментаря
        comment = QtWidgets.QTextEdit()
        comment.setPlaceholderText("Коментар...")
        comment.setMaximumHeight(60)


        f.addRow("Ім'я:", name)
        f.addRow("Кількість людей:", ppl)
        f.addRow("Тип місця:", type_btn)
        f.addRow("Коментар:", comment)
        lay.addLayout(f)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        # Збільшити кнопки
        for button in btns.buttons():
            button.setMinimumHeight(35)
            button.setMinimumWidth(100)
        lay.addWidget(btns)

        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.counter += 1
            place_key = 'ps5' if get_type_index() == 1 else 'table'
            place_name = "PlayStation5" if place_key == 'ps5' else "звичайний стіл"
            s = Session(
                sid=self.counter,
                name=name.text().strip() or f"Клієнт {self.counter}",
                place_type=place_key,
                comment = comment.toPlainText().strip()
            )
            s.batches.append(Batch(count=ppl.value(), start=datetime.now(),comment=""))
            self.sessions[s.sid] = s
            self.refresh_rows()
            # Повідомлення з коментарем
            if s.comment:
                self.status_bar.showMessage(
                    f"✓ Додано стіл #{s.sid} ({place_name}), {ppl.value()} людей (💬 {s.comment[:30]}...)",
                    3000
                )
            else:
                self.status_bar.showMessage(
                    f"✓ Додано стіл #{s.sid} ({place_name}), {ppl.value()} людей",
                    3000
                )

    def closeEvent(self, event):
        """Зберігаємо сесії при закритті"""

        reply = QtWidgets.QMessageBox.question(
            self,
            "Підтвердження виходу",
            "Певний, що хочеш закрити програму?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            save_active_sessions(self.sessions, self.counter)
            event.accept()  # allow closing
        else:
            event.ignore()  # cancel closing


    # main_window.py - частина 2
    """Додаткові методи для ClubBillingApp"""

    # Додайте ці методи до класу ClubBillingApp з частини 1
    def manual_save(self):
        """Ручне збереження даних"""
        try:
            save_active_sessions(self.sessions, self.counter)
            QtWidgets.QMessageBox.information(
                self,
                "Збереження",
                f"✓ Успішно збережено {len(self.sessions)} столів!"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Помилка",
                f"Не вдалося зберегти дані:\n{e}"
            )

    def autosave(self):
        """Автоматичне збереження кожні 5 хвилин"""
        if self.sessions:
            try:
                save_active_sessions(self.sessions, self.counter)
                self.status_bar.showMessage(
                    f"💾 Автозбереження: {len(self.sessions)} столів", 3000
                )
            except Exception as e:
                print(f"❌ Помилка автозбереження: {e}")

    def add_people_to_selected(self):
        """Додати людей до обраного столу"""
        s = self._selected_session()
        if not s:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Оберіть стіл для додавання людей"
            )
            return
        cnt, ok = QtWidgets.QInputDialog.getInt(
            self, "Додати людей", "Кількість:", 1, 1, 50, 1
        )
        if ok and cnt > 0:
            s.batches.append(Batch(count=cnt, start=datetime.now()))
            self.refresh_rows()
            self.status_bar.showMessage(
                f"✓ Додано {cnt} людей до столу #{s.sid}", 3000
            )

    def settle_one_from_selected(self):
        """Розрахувати одну людину"""
        s = self._selected_session()
        if not s:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Оберіть стіл для розрахунку"
            )
            return
        if len(s.batches) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Номежливо розрахувати одного, оскільки люди приходили "
                "в різний час. Скористуйся Частковою оплатою столу."
            )
            return
        if s.total_people() == 0:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "На столі немає людей"
            )
            return
        weekday = UA_WEEKDAYS[datetime.now().weekday()]
        amount = s.settle_one(weekday, self.round_step, self.tariffs)
        if amount <= 0:
            return
        disc = min(100, max(0, self.global_discount + s.discount_pct))
        amount = int(round(amount * (100 - disc) / 100.0))
        QtWidgets.QMessageBox.information(
            self, "Оплата 1 людини",
            f"До сплати: {amount} грн"
        )
        save_closed_session(
            s.sid, s.name, 1, amount, "one", s.place_type
        )
        self.refresh_rows()
        self.status_bar.showMessage(
            f"✓ Оплачено {amount} грн (стіл #{s.sid}, 1 людина)", 3000
        )

    def edit_selected_session(self):
        """Редагувати обраний стіл"""
        s = self._selected_session()
        if not s:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Оберіть стіл для редагування"
            )
            return

        # Просте вікно підтвердження
        reply = QtWidgets.QMessageBox.question(
            self,
            "⚠️ Підтвердження",
            f"Редагувати стіл <b>#{s.sid} ({s.name})</b>?<br><br>"
            f"<span style='color: #dc2626;'>Це може вплинути на розрахунки!</span>",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No  # За замовчуванням "Ні"
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Якщо підтвердив - відкриваємо діалог
        dlg = EditSessionDialog(s, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.refresh_rows()
            self.status_bar.showMessage(
                f"✓ Стіл #{s.sid} оновлено", 3000
            )

    '''def close_selected_session(self):
        """Закрити обраний стіл"""
        s = self._selected_session()
        if not s:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Оберіть стіл для закриття"
            )
            return
        weekday = UA_WEEKDAYS[datetime.now().weekday()]
        dlg = PartialBillDialog(s, weekday, self.round_step, self.tariffs, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if s.total_people() == 0:
                del self.sessions[s.sid]
                self.status_bar.showMessage(
                    f"✓ Стіл #{s.sid} закрито", 3000
                )
            else:
                self.status_bar.showMessage(
                    f"✓ Часткова оплата для столу #{s.sid}", 3000
                )
            self.refresh_rows()'''

    def _selected_session(self) -> Session | None:
        """Отримати обраний стіл"""
        r = self.table.currentRow()
        if r < 0:
            return None
        sid_item = self.table.item(r, 0)
        if not sid_item:
            return None
        sid = sid_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if sid is None:
            text = sid_item.text().split()[0]
            sid = int(text)
        return self.sessions.get(sid)

    def _add_people_by_id(self, sid: int):
        s = self.sessions.get(sid)
        if not s:
            return

        dlg = AddPeopleDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            cnt = dlg.get_count()
            comment = dlg.get_comment()
            s.batches.append(Batch(count=cnt, start=datetime.now(), comment=comment))
            self.refresh_rows()

            # Показуємо повідомлення з коментарем якщо є
            if comment:
                self.status_bar.showMessage(f"✓ Додано {cnt} людей до столу #{sid} (💬 {comment[:30]}...)", 3000)
            else:
                self.status_bar.showMessage(f"✓ Додано {cnt} людей до столу #{sid}", 3000)

    def _add_people_by_id_and_select(self, sid: int, row: int):
        """Додати людей і зберегти виділення"""
        self.table.selectRow(row)
        self._add_people_by_id(sid)

    '''def _settle_one_by_id(self, sid: int, row: int):
        """Розрахувати 1 людину за ID"""
        self.table.selectRow(row)
        s = self.sessions.get(sid)
        if not s:
            return
        if len(s.batches) > 1:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "Номежливо розрахувати одного, оскільки люди приходили "
                "в різний час. Скористуйся Частковою оплатою столу."
            )
            return
        if s.total_people() == 0:
            QtWidgets.QMessageBox.warning(
                self, "Помилка",
                "На столі немає людей"
            )
            return
        weekday = UA_WEEKDAYS[datetime.now().weekday()]
        amount = s.settle_one(weekday, self.round_step, self.tariffs)
        if amount <= 0:
            return
        disc = min(100, max(0, self.global_discount + s.discount_pct))
        amount = int(round(amount * (100 - disc) / 100.0))
        QtWidgets.QMessageBox.information(
            self, "Оплата 1 людини",
            f"До сплати: {amount} грн"
        )
        save_closed_session(
            s.sid, s.name, 1, amount, "one", s.place_type
        )
        self.refresh_rows()
        self.status_bar.showMessage(
            f"✓ Оплачено {amount} грн (стіл #{s.sid}, 1 людина)", 3000
        )'''

    def _partial_bill_by_id(self, sid: int, row: int):
        """Частковий розрахунок за ID"""
        self.table.selectRow(row)
        s = self.sessions.get(sid)
        if not s:
            return
        weekday = UA_WEEKDAYS[datetime.now().weekday()]
        dlg = PartialBillDialog(s, weekday, self.tariffs, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if s.total_people() == 0:
                del self.sessions[s.sid]
                self.status_bar.showMessage(
                    f"✓ Стіл #{s.sid} закрито", 3000
                )
            else:
                self.status_bar.showMessage(
                    f"✓ Часткова оплата для столу #{s.sid}", 3000
                )
            self.refresh_rows()


    def _edit_by_id(self, sid: int, row: int):
        """Редагувати за ID"""
        self.table.selectRow(row)
        s = self.sessions.get(sid)
        if not s:
            return
        # Просте вікно підтвердження
        reply = QtWidgets.QMessageBox.question(
            self,
            "⚠️ Підтвердження",
            f"Редагувати стіл <b>#{s.sid} ({s.name})</b>?<br><br>"
            f"<span style='color: #dc2626;'>Це може вплинути на розрахунки!</span>",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No  # За замовчуванням "Ні"
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        dlg = EditSessionDialog(s, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.refresh_rows()
            self.status_bar.showMessage(
                f"✓ Стіл #{s.sid} оновлено", 3000
            )

    def _close_by_id(self, sid: int, row: int):
        """Повна сплата і закриття стіл за ID"""
        self.table.selectRow(row)
        s = self.sessions.get(sid)
        if not s:
            return

        if s.total_people() == 0:
            del self.sessions[s.sid]
            self.refresh_rows()
            self.status_bar.showMessage(
                f"✓ Стіл #{s.sid} закрито", 3000
            )
        else:
            # Показуємо діалог повного розрахунку
            weekday = UA_WEEKDAYS[datetime.now().weekday()]
            dlg = FullBillDialog(s, weekday, self.round_step, self.tariffs, self)
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                del self.sessions[s.sid]
                self.refresh_rows()
                self.status_bar.showMessage(f"✓ Стіл #{s.sid} закрито", 3000)

    # main_window.py - частина 3
    """Оновлення таблиці та діалоги налаштувань"""

    # Додайте ці методи до класу ClubBillingApp

    def refresh_rows(self):
        """Оновлення таблиці столів"""
        self.table.setRowCount(0)
        weekday = UA_WEEKDAYS[datetime.now().weekday()]

        sorted_sessions = sorted(self.sessions.values(), key=lambda s: s.sid)
        total_people_count = 0

        for s in sorted_sessions:
            total_people = s.total_people()
            total_people_count += total_people

            if s.batches:
                oldest = min(s.batches, key=lambda b: b.start)
                mins = int((datetime.now() - oldest.start).total_seconds() // 60)
                hhmm = f"{mins // 60:02d}:{mins % 60:02d}"
            else:
                hhmm = "00:00"

            r = self.table.rowCount()
            self.table.insertRow(r)

            # ID з іконкою
            id_text = f"{s.sid} {' 🎮' if s.place_type == 'ps5' else ' 🎲'}"
            id_item = QtWidgets.QTableWidgetItem(id_text)
            id_item.setData(QtCore.Qt.ItemDataRole.UserRole, s.sid)
            font = id_item.font()
            font.setPointSize(12)  # Set your desired size
            id_item.setFont(font)
            self.table.setItem(r, 0, id_item)

            # Ім'я зі знижкою
            name_item = QtWidgets.QTableWidgetItem(s.name)
            #if s.discount_pct > 0:
            #    name_item.setText(f"{s.name} (-{s.discount_pct}%)")
            #    name_item.setForeground(QtGui.QColor("#2563eb"))

            #name_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            # Додаємо коментар як tooltip
            if s.comment:
                name_item.setToolTip(f"💬 {s.comment}")


            self.table.setItem(r, 1, name_item)

            total_people_item = QtWidgets.QTableWidgetItem(str(total_people))
            total_people_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, total_people_item)

            time_item = QtWidgets.QTableWidgetItem(hhmm)
            time_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 3, time_item)
            hours_rounded = s.get_hours()
            hours_rounded_item = QtWidgets.QTableWidgetItem(str(hours_rounded))
            hours_rounded_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 4, hours_rounded_item)
            sum_amount = s.total_amount(
                weekday=weekday,
                round_step=AppConfig.hour_step,
                tariffs=self.tariffs
            )
            sum_amount_item = QtWidgets.QTableWidgetItem(str(sum_amount))
            sum_amount_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 5, sum_amount_item)

            # Коментар
            # Відображаємо всі коментарі (сесія + батчі)
            all_comments = []
            if s.comment:
                all_comments.append(f"📋 {s.comment}")
            for idx, b in enumerate(s.batches, 1):
                if b.comment:
                    all_comments.append(f"#{idx}: {b.comment}")

            comments_text = "\n".join(all_comments) if all_comments else ""
            comment_item = QtWidgets.QTableWidgetItem(comments_text)
            font = comment_item.font()
            font.setPointSize(13)  # Set your desired size
            comment_item.setFont(font)
            comment_item.setToolTip(comments_text)  # Tooltip для довгих коментарів
            self.table.setItem(r, 6, comment_item)

            # Кнопки дій
            self._create_action_buttons(r, s.sid)

        # Оновлення статистики
        self.lbl_active.setText(f"Активних столів: {len(self.sessions)}")
        self.lbl_people.setText(f"Всього людей: {total_people_count}")

    def _create_action_buttons(self, row: int, sid: int):
        """Створення кнопок дій для рядка"""
        buttons = [
            (7, "+", "Додати людей", "#1AD95D", "#038C25", None, 25, 25,
             lambda: self._add_people_by_id_and_select(sid, row)),
            (9, "🪙", "Частковий розрахунок", "#04B2D9", "#049DD9", None, 25, 20,
             lambda: self._partial_bill_by_id(sid, row)),
            (8, "✏️", "Редагувати", "#D7F205", "#F28705", None, 25, 20,
             lambda: self._edit_by_id(sid, row)),
            (10, "💵", "Повна оплата", "#04BFBF", "#03A6A6", None, 25, 20,
             lambda: self._close_by_id(sid, row)),
        ]

        for col, text, tooltip, bg, hover_bg, width, height, font_size, handler in buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            if width:
                btn.setFixedSize(width, height)
            else:
                btn.setFixedHeight(height)
            btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg};
                        color: "white";
                        border: none;
                        border-radius: 4px;
                        font-size: {font_size}px;
                        {'font-weight: bold;' if col == 4 else ''}
                    }}
                    QPushButton:hover {{
                        background: {hover_bg};
                    }}
                """)
            btn.clicked.connect(handler)
            self.table.setCellWidget(row, col, btn)

    def open_tariffs(self):
        """Діалог редагування тарифів"""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Редагування тарифів")
        dlg.resize(700, 400)
        lay = QtWidgets.QVBoxLayout(dlg)

        top = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Тип місця:")
        selector_btn, get_selector_index = create_choice_button(
            ["Звичайні столи", "PlayStation5"], 0
        )
        top.addWidget(lbl)
        top.addWidget(selector_btn)
        top.addStretch()
        lay.addLayout(top)

        table = QtWidgets.QTableWidget(8, 7)
        table.setHorizontalHeaderLabels(UA_WEEKDAYS)
        table.setVerticalHeaderLabels(HOUR_LABELS)
        lay.addWidget(table)

        # Оригінальні значення
        original_tariffs = {
            "table": {day: list(rates) for day, rates in self.tariffs["table"].items()},
            "ps5": {day: list(rates) for day, rates in self.tariffs["ps5"].items()}
        }

        def load_for(idx=0):
            kind = "table" if idx == 0 else "ps5"
            for r in range(8):
                for c, day in enumerate(UA_WEEKDAYS):
                    val = self.tariffs[kind][day][r]
                    item = QtWidgets.QTableWidgetItem(str(val))
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    table.setItem(r, c, item)

        '''def on_type_changed():
            load_for(get_selector_index())

        selector_btn.menu().triggered.connect(on_type_changed)
        load_for(0)

        b = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(b)
    
        '''

        def on_type_changed(action):
            # Get index from the action that was just triggered
            menu = selector_btn.menu()
            index = menu.actions().index(action)
            load_for(index)

        selector_btn.menu().triggered.connect(on_type_changed)
        load_for(0)

        b = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(b)
        def save():
            kind = "table" if get_selector_index() == 0 else "ps5"
            try:
                for r in range(8):
                    for c, day in enumerate(UA_WEEKDAYS):
                        it = table.item(r, c)
                        val = int(it.text()) if it and it.text().strip() else 0
                        self.tariffs[kind][day][r] = max(0, val)
                save_tariffs(self.tariffs)
                QtWidgets.QMessageBox.information(
                    self, "Успішно",
                    "Тарифи збережено"
                )
                dlg.accept()
            except ValueError:
                QtWidgets.QMessageBox.critical(
                    self, "Помилка",
                    "Введіть тільки числові значення!"
                )
                return

        def cancel():
            self.tariffs = original_tariffs
            dlg.reject()

        b.accepted.connect(save)
        b.rejected.connect(cancel)
        dlg.exec()

    def open_settings(self):
        """Діалог налаштувань"""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Налаштування")
        dlg.resize(400, 200)
        lay = QtWidgets.QVBoxLayout(dlg)

        f = QtWidgets.QFormLayout()

        disc = QtWidgets.QSpinBox()
        disc.setRange(0, 100)
        disc.setSuffix("%")
        disc.setValue(self.global_discount)

        current_round_idx = {60: 0, 30: 1, 15: 2}.get(self.round_step, 0)
        round_btn, get_round_index = create_choice_button([
            "До 1 години (60 хв)",
            "До 30 хвилин",
            "До 15 хвилин"
        ], current_round_idx)

        f.addRow("Глобальна знижка:", disc)
        f.addRow("Округлення часу:", round_btn)
        lay.addLayout(f)

        info = QtWidgets.QLabel(
            "💡 Глобальна знижка додається до знижки столу.\n"
            "Округлення визначає мінімальний крок розрахунку."
        )
        info.setStyleSheet(
            "color: #666; padding: 10px; background: #f0f0f0; border-radius: 5px;"
        )
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addStretch()

        b = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(b)

        def ok():
            self.global_discount = disc.value()
            self.round_step = {0: 60, 1: 30, 2: 15}[get_round_index()]
            QtWidgets.QMessageBox.information(
                self, "Успішно",
                "Налаштування збережено"
            )
            dlg.accept()

        b.accepted.connect(ok)
        b.rejected.connect(dlg.reject)
        dlg.exec()

    def show_shortcuts(self):
        """Показати клавіатурні скорочення"""
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Клавіатурні скорочення")
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText(
            "<b>Доступні клавіатурні скорочення:</b><br><br>"
            "<b>Ctrl+N</b> — Додати новий стіл<br>"
            "<b>Ctrl+S</b> — Зберегти дані<br>"
           # "<b>Ctrl+E</b> — Редагувати обраний стіл<br>"
            "<b>Ctrl+T</b> — Відкрити тарифи<br>"
            "<b>Ctrl+,</b> — Налаштування<br>"
           # "<b>Delete</b> — Закрити обраний стіл<br><br>"
            "<i>Подвійний клік на рядку — редагування столу</i><br>"
            "<i>Автозбереження раз на хвилину</i>"
        )
        msg.exec()