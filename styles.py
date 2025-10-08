# styles.py
"""Стилі інтерфейсу"""

from PyQt6 import QtWidgets


def apply_global_style(app: QtWidgets.QApplication):
    """Застосовує глобальні стилі до додатку"""
    style = """
    QWidget { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                   stop:0 #f6f7f9, stop:1 #eef1f6); 
        font-family: 'Segoe UI', 'Helvetica Neue', Arial; 
    }
    QMainWindow { background: transparent; }
    QTableWidget { 
        background: transparent; 
        border: none; 
        selection-background-color: #cfe8ff;
        font-size: 15px;
    }
    QTableWidget::item { 
        padding: 2px;
        font-size: 14px;
    }
    QHeaderView::section { 
        background: #2b7cff; 
        color: white; 
        padding: 6px; 
        border: none; 
        font-weight:600; 
    }
    QPushButton { 
        background: white; 
        border: 2px solid #c8d6e5; 
        padding: 5px 2px; 
        border-radius: 8px;
        font-size: 13px;
        min-height: 25px;
    }
    QPushButton:hover { background: #f0f4f8; }
    QPushButton#primary { 
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1, 
                                   stop:0 #3b82f6, stop:1 #2563eb); 
        color: white; 
        border: none; 
    }
    QPushButton#primary:hover { 
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1, 
                                   stop:0 #4a90ff, stop:1 #3b82f6); 
    }
    QPushButton#danger { 
        background: #ff6b6b; 
        color: white; 
        border: none; 
    }
    QPushButton#danger:hover { background: #ff5252; }
    QLabel.title { font-size: 16px; font-weight: 700; }
    QLabel.subtitle { color: #555; }

    QLineEdit, QSpinBox, QComboBox { 
        background: white; 
        border: 1px solid #d6dde8; 
        padding: 6px; 
        border-radius: 6px; 
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus { 
        border: 2px solid #3b82f6; 
    }

    QMenu { background: white; border: 1px solid #d6dde8; }
    QMenu::item { padding: 8px 20px; }
    QMenu::item:selected { background: #e3f2fd; color: #1e293b; }

    QDialog { 
        background: white;
    }
    QDialog QLabel {
        font-size: 13px;
    }
    QPlainTextEdit { background: white; border: 1px solid #d6dde8; }
    """
    app.setStyleSheet(style)