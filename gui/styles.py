"""
Audio Kit Design System - Teenage Engineering & Braun / Dieter Rams Aesthetic
- Matte warm off-black / deep graphite chassis (#121214, #18181A)
- Tactile, recessed panels with micro-borders (#28282C)
- High contrast typography (clean geometric sans-serif / monospace accents)
- Teenage Engineering signature punctuation accents: Signal Orange (#FF4800 / #FF5722), Acid Yellow/Cream (#FFF8E7), Warm Gray (#8E8E93)
- Mechanical, purposeful buttons and segmented status pills
"""

STYLE_QSS = """
* {
    font-family: -apple-system, "SF Pro Display", "SF Pro Text", "Segoe UI", "Inter", sans-serif;
    font-size: 12px;
    color: #ECECED;
    outline: none;
}

QMainWindow, QWidget#MainContainer {
    background-color: #0E0E10;
}

/* Sidebar navigation - Industrial pocket-operator / TP-7 inspired */
QFrame#Sidebar {
    background-color: #151518;
    border-right: 1px solid #242428;
}

QLabel#AppBrand {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #FFFFFF;
    text-transform: uppercase;
}

QLabel#BrandTag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #FF5722; /* TE Orange */
    text-transform: uppercase;
    background-color: #241A16;
    border: 1px solid #452419;
    border-radius: 3px;
    padding: 2px 6px;
}

QPushButton.NavBtn {
    background-color: transparent;
    color: #8A8A93;
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    border: 1px solid transparent;
}

QPushButton.NavBtn:hover {
    background-color: #1C1C20;
    color: #FFFFFF;
    border-color: #2D2D34;
}

QPushButton.NavBtn:checked {
    background-color: #202026;
    color: #FFFFFF;
    border-left: 3px solid #FF5722;
    border-top: 1px solid #2E2E36;
    border-right: 1px solid #2E2E36;
    border-bottom: 1px solid #2E2E36;
}

/* Content Area */
QFrame#ContentFrame {
    background-color: #0E0E10;
}

/* Tactile Cards & Panels */
QFrame.Card {
    background-color: #151518;
    border: 1px solid #242428;
    border-radius: 8px;
}

/* Drop Zone - Industrial Recessed Plate */
QFrame.DropZone {
    background-color: #121215;
    border: 1px dashed #303038;
    border-radius: 8px;
}

QFrame.DropZone:hover {
    border: 1px solid #FF5722;
    background-color: #16161B;
}

/* Headings */
QLabel.ViewHeader {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.2px;
    color: #FFFFFF;
}

QLabel.ViewSubheader {
    font-size: 11px;
    font-weight: 500;
    color: #7A7A85;
    letter-spacing: 0.2px;
}

/* Form Inputs - Sleek Tactile Grooves */
QLineEdit {
    background-color: #121215;
    border: 1px solid #26262C;
    border-radius: 5px;
    padding: 7px 10px;
    color: #F0F0F2;
    font-size: 12px;
    selection-background-color: #FF5722;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #FF5722;
    background-color: #16161A;
}

/* Physical Instrument-Style Buttons */
QPushButton.PrimaryBtn {
    background-color: #FF5722; /* TE Accent */
    color: #FFFFFF;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    border-radius: 6px;
    padding: 9px 18px;
    border: 1px solid #FF6E3D;
}

QPushButton.PrimaryBtn:hover {
    background-color: #F4450E;
}

QPushButton.PrimaryBtn:pressed {
    background-color: #D63704;
}

QPushButton.PrimaryBtn:disabled {
    background-color: #222226;
    color: #55555C;
    border: 1px solid #2C2C33;
}

QPushButton.SecondaryBtn {
    background-color: #1E1E23;
    color: #ECECED;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.4px;
    border-radius: 6px;
    padding: 8px 14px;
    border: 1px solid #2A2A32;
}

QPushButton.SecondaryBtn:hover {
    background-color: #27272E;
    border-color: #3E3E49;
    color: #FFFFFF;
}

QPushButton.SecondaryBtn:pressed {
    background-color: #18181D;
}

QPushButton.GhostBtn {
    background-color: transparent;
    color: #92929D;
    font-weight: 500;
    font-size: 11px;
    border-radius: 5px;
    padding: 6px 10px;
    border: 1px solid #282830;
}

QPushButton.GhostBtn:hover {
    background-color: #1A1A1F;
    color: #FF5722;
    border-color: #3D3D48;
}

/* Minimal Hardware Table */
QTableWidget {
    background-color: #151518;
    border: 1px solid #242428;
    border-radius: 8px;
    gridline-color: #1D1D22;
    selection-background-color: #23232B;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #111114;
    color: #72727D;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #242428;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* Hardware Gauge Progress Bar */
QProgressBar {
    background-color: #121215;
    border: 1px solid #26262C;
    border-radius: 4px;
    height: 8px;
    text-align: right;
}

QProgressBar::chunk {
    background-color: #FF5722;
    border-radius: 3px;
}

/* Monospace Diagnostics Terminal */
QTextEdit#LogConsole {
    background-color: #0B0B0D;
    border: 1px solid #1F1F24;
    border-radius: 6px;
    color: #8C8C96;
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace;
    font-size: 11px;
    padding: 8px 12px;
}

/* Thin precision scrollbar */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2D2D35;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #FF5722;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
