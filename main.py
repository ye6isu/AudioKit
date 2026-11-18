"""
Main Window for Audio Kit
Hosts sidebar navigation and dedicated functional views.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from gui.styles import STYLE_QSS
from gui.tab_metadata import MetadataEditorTab
from gui.tab_walkman import WalkmanFixerTab
from gui.tab_replaygain import ReplayGainTab
from gui.tab_transfer import ArtTransferTab

class AudioKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Kit")
        self.resize(1080, 720)
        self.setMinimumSize(920, 600)

        # Main Central Container
        central_widget = QWidget()
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 24, 16, 24)
        side_layout.setSpacing(8)

        # Branding
        title_label = QLabel("Audio Kit")
        title_label.setObjectName("AppTitle")
        sub_label = QLabel("Audio & Metadata Studio")
        sub_label.setObjectName("AppSubtitle")
        side_layout.addWidget(title_label)
        side_layout.addWidget(sub_label)

        # Nav Buttons
        self.nav_buttons = []
        nav_items = [
            ("🏷️  Metadata & Art", 0),
            ("✨  Walkman Fixer", 1),
            ("📊  ReplayGain 2.0", 2),
            ("🔄  Art Transfer", 3)
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_tab(idx))
            self.nav_buttons.append(btn)
            side_layout.addWidget(btn)

        side_layout.addStretch()

        # Footer Info
        footer = QLabel("v1.0.0 • EBU R128 & Baseline JPEG")
        footer.setStyleSheet("color: #475569; font-size: 10px; padding-left: 4px;")
        side_layout.addWidget(footer)

        root_layout.addWidget(sidebar)

        # --- Content Area (Stacked Widget) ---
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentFrame")

        self.tab_metadata = MetadataEditorTab()
        self.tab_walkman = WalkmanFixerTab()
        self.tab_replaygain = ReplayGainTab()
        self.tab_transfer = ArtTransferTab()

        self.content_stack.addWidget(self.tab_metadata)
        self.content_stack.addWidget(self.tab_walkman)
        self.content_stack.addWidget(self.tab_replaygain)
        self.content_stack.addWidget(self.tab_transfer)

        root_layout.addWidget(self.content_stack)

        # Default select first tab
        self._switch_tab(0)

    def _switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_QSS)
    window = AudioKitMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
