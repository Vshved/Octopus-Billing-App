# styles.py
"""Стилі інтерфейсу - компактна версія"""

from PyQt6 import QtWidgets


def apply_global_style(app: QtWidgets.QApplication):
    """Застосовує глобальні стилі до додатку"""
    style = """
    QWidget { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                   stop:0 #f6f7f9, stop:1 #eef1f6); 
        font-family: 'Segoe UI', 'Helvetica Neue', Arial; 
        font-size: 12px;
    }
    QMainWindow { background: transparent; }
    QTableWidget { 
        background: white; 
        color: #1e293b;
        border: none; 
        selection-background-color: #cfe8ff;
        selection-color:  #1e293b;;
        font-size: 15px;
        
        
    }
    QTableWidget::item { 
        padding: 8px;
        font-size: 15px;
        color: black;
        border: 1px solid white; 
         
        
        
    }
    QHeaderView::section { 
        background: #2b7cff; 
        color: white; 
        padding: 5px; 
        border: 1px solid #d6dde8; 
        font-weight: 600;
        font-size: 11px;
    }
    QPushButton { 
        background: white; 
        color: black;
        border: 2px solid #c8d6e5; 
        padding: 4px 8px; 
        border-radius: 6px;
        font-size: 12px;
        min-height: 22px;
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
    QLabel.title { font-size: 14px; font-weight: 700; }
    QLabel.subtitle { color: #555; font-size: 11px; }

    QLineEdit, QSpinBox, QComboBox, QTimeEdit { 
        background: white; 
        color: black;
        border: 1px solid #d6dde8; 
        padding: 2px; 
        border-radius: 2px;
        font-size: 14px;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus,QTimeEdit:focus  { 
        border: 1px solid #d6dde8;  
        color: black;
        background: white; 
        
     QTimeEdit::up-button, QTimeEdit::down-button {
        background: #e5e7eb;
        border: none;
    }
    QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
        background: #d1d5db;
    }   
    

    QMenu { 
        background: white; 
        border: 1px solid #d6dde8;
        font-size: 14px;
        color: black;
    }
    QMenu::item { padding: 2px 8px; }
    QMenu::item:selected { background: white; color: black; }

    QDialog { 
        background: white;
        color: black;
    }
    QDialog QLabel {
        font-size: 12px;
        color: black;
    }
    QPlainTextEdit, QTextEdit { 
        background: white; 
        border: 1px solid #d6dde8;
        font-size: 12px;
        padding: 4px;
        color: black;
    }
    QGroupBox {
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #d6dde8;
        border-radius: 5px;
        margin-top: 8px;
        padding-top: 8px;
        color: black;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        
        color: black;
    }
    QFormLayout {
        spacing: 5px;
        color: black;
    }
    QStatusBar {
        font-size: 11px;
        color: black;
    }
    """
    app.setStyleSheet(style)