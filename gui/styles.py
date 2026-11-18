"""
Audio Kit - High-contrast tactile Dark Theme (Apple & Teenage Engineering inspired)
"""

STYLE_QSS = """
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    color: #EDEDED;
    outline: none;
}

QMainWindow, QWidget#MainContainer, QStackedWidget#ContentFrame {
    background-color: #121214;
}

/* Sidebar */
QFrame#Sidebar {
    background-color: #18181B;
    border-right: 1px solid #27272A;
}

QLabel#AppBrand {
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.5px;
}

/* Nav items */
QPushButton[class~="NavBtn"] {
    background-color: transparent;
    color: #A1A1AA;
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    border: none;
}

QPushButton[class~="NavBtn"]:hover {
    background-color: #27272A;
    color: #FFFFFF;
}

QPushButton[class~="NavBtn"]:checked {
    background-color: #27272A;
    color: #FF5500;
    font-weight: 600;
    border-left: 3px solid #FF5500;
}

/* Cards & Panels */
QFrame[class~="Card"] {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
}

/* Drop Zone */
QFrame[class~="DropZone"] {
    background-color: #18181B;
    border: 1px dashed #3F3F46;
    border-radius: 8px;
}

QFrame[class~="DropZone"]:hover {
    border: 1px dashed #FF5500;
    background-color: #202024;
}

/* View Header */
QLabel[class~="ViewHeader"] {
    font-size: 18px;
    font-weight: 700;
    color: #FFFFFF;
}

/* Form Inputs */
QLineEdit {
    background-color: #121214;
    border: 1px solid #3F3F46;
    border-radius: 5px;
    padding: 6px 10px;
    color: #FFFFFF;
    font-size: 12px;
}

QLineEdit:focus {
    border: 1px solid #FF5500;
    background-color: #18181B;
}

/* Primary Button */
QPushButton[class~="PrimaryBtn"] {
    background-color: #FF5500;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    border-radius: 6px;
    padding: 8px 16px;
    border: none;
}

QPushButton[class~="PrimaryBtn"]:hover {
    background-color: #E64D00;
}

QPushButton[class~="PrimaryBtn"]:pressed {
    background-color: #CC4400;
}

QPushButton[class~="PrimaryBtn"]:disabled {
    background-color: #27272A;
    color: #52525B;
}

/* Secondary Button */
QPushButton[class~="SecondaryBtn"] {
    background-color: #27272A;
    color: #EDEDED;
    font-weight: 500;
    font-size: 12px;
    border-radius: 6px;
    padding: 8px 14px;
    border: 1px solid #3F3F46;
}

QPushButton[class~="SecondaryBtn"]:hover {
    background-color: #323238;
    color: #FFFFFF;
}

/* Ghost Button */
QPushButton[class~="GhostBtn"] {
    background-color: #27272A;
    color: #D4D4D8;
    font-size: 11px;
    font-weight: 500;
    border-radius: 5px;
    padding: 5px 12px;
    border: 1px solid #3F3F46;
}

QPushButton[class~="GhostBtn"]:hover {
    background-color: #3F3F46;
    color: #FFFFFF;
}

/* Tables */
QTableWidget {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    gridline-color: #27272A;
    selection-background-color: #2E2E33;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #121214;
    color: #A1A1AA;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #27272A;
    font-weight: 600;
    font-size: 11px;
}

/* Progress Bar */
QProgressBar {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 4px;
    height: 6px;
    text-align: right;
}

QProgressBar::chunk {
    background-color: #FF5500;
    border-radius: 3px;
}

/* Monospace Console */
QTextEdit#LogConsole {
    background-color: #0E0E10;
    border: 1px solid #27272A;
    border-radius: 6px;
    color: #A1A1AA;
    font-family: Consolas, monospace;
    font-size: 11px;
    padding: 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
}

QScrollBar::handle:vertical {
    background: #3F3F46;
    min-height: 20px;
    border-radius: 3px;
}
"""
