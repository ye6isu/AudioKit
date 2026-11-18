"""
Audio Kit Stylesheet
Clean, minimalist dark styling inspired by Apple design language (SF/San Francisco aesthetics, subtle borders, high legibility).
"""

STYLE_QSS = """
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #E2E8F0;
}

QMainWindow, QWidget#MainContainer {
    background-color: #0F1117;
}

/* Sidebar navigation */
QFrame#Sidebar {
    background-color: #161822;
    border-right: 1px solid #232736;
}

QLabel#AppTitle {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.5px;
    padding-left: 4px;
}

QLabel#AppSubtitle {
    font-size: 11px;
    color: #718096;
    padding-left: 4px;
    margin-bottom: 12px;
}

QPushButton.NavBtn {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    border: none;
}

QPushButton.NavBtn:hover {
    background-color: #1E2230;
    color: #F8FAFC;
}

QPushButton.NavBtn:checked {
    background-color: #2D3748;
    color: #38BDF8;
    font-weight: 600;
}

/* Content areas */
QFrame#ContentFrame {
    background-color: #0F1117;
}

/* Drop Areas & Cards */
QFrame.Card {
    background-color: #161822;
    border: 1px solid #232736;
    border-radius: 12px;
}

QFrame.DropZone {
    background-color: #13151F;
    border: 2px dashed #2E3446;
    border-radius: 12px;
}

QFrame.DropZone:hover {
    border-color: #38BDF8;
    background-color: #171A27;
}

/* Headers */
QLabel.SectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #F8FAFC;
}

QLabel.SectionDesc {
    font-size: 12px;
    color: #94A3B8;
}

/* Inputs & Form Fields */
QLineEdit {
    background-color: #1A1D2A;
    border: 1px solid #2D3345;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F8FAFC;
    selection-background-color: #38BDF8;
    selection-color: #0F1117;
}

QLineEdit:focus {
    border: 1px solid #38BDF8;
    background-color: #1E2232;
}

/* Buttons */
QPushButton.PrimaryBtn {
    background-color: #38BDF8;
    color: #0F1117;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 18px;
    border: none;
}

QPushButton.PrimaryBtn:hover {
    background-color: #7DD3FC;
}

QPushButton.PrimaryBtn:pressed {
    background-color: #0284C7;
}

QPushButton.PrimaryBtn:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton.SecondaryBtn {
    background-color: #1E2230;
    color: #E2E8F0;
    font-weight: 500;
    border-radius: 8px;
    padding: 8px 16px;
    border: 1px solid #2D3345;
}

QPushButton.SecondaryBtn:hover {
    background-color: #272C3E;
    border-color: #3F465C;
}

QPushButton.SecondaryBtn:pressed {
    background-color: #1A1D2A;
}

QPushButton.DangerBtn {
    background-color: #EF4444;
    color: #FFFFFF;
    font-weight: 600;
    border-radius: 8px;
    padding: 6px 12px;
    border: none;
}

QPushButton.DangerBtn:hover {
    background-color: #DC2626;
}

/* Tables and Lists */
QTableWidget, QListWidget {
    background-color: #161822;
    border: 1px solid #232736;
    border-radius: 8px;
    gridline-color: #1E2230;
    selection-background-color: #272C3E;
    selection-color: #38BDF8;
}

QHeaderView::section {
    background-color: #13151F;
    color: #94A3B8;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #232736;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}

/* Progress Bar */
QProgressBar {
    background-color: #1A1D2A;
    border: 1px solid #2D3345;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    font-size: 10px;
    font-weight: 600;
    color: #FFFFFF;
}

QProgressBar::chunk {
    background-color: #38BDF8;
    border-radius: 5px;
}

/* Log and Console View */
QTextEdit#LogConsole {
    background-color: #10121A;
    border: 1px solid #1E2230;
    border-radius: 8px;
    color: #94A3B8;
    font-family: Consolas, "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0F1117;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2D3345;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #3F465C;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
