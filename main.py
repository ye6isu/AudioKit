"""
Audio Kit Main Application Window (Clean, de-cluttered)
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt

from gui.styles import STYLE_QSS
from gui.tab_metadata import MetadataEditorTab
from gui.tab_walkman import BaselineConverterTab
from gui.tab_replaygain import ReplayGainTab
from gui.tab_transfer import ArtTransferTab

class AudioKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Kit")
        self.resize(1020, 680)
        self.setMinimumSize(900, 580)

        central_widget = QWidget()
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 20, 14, 20)
        side_layout.setSpacing(6)

        title_label = QLabel("Audio Kit")
        title_label.setObjectName("AppBrand")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-bottom: 12px; padding-left: 6px;")
        side_layout.addWidget(title_label)

        # Nav items
        self.nav_buttons = []
        nav_items = [
            ("Metadata", 0),
            ("Baseline Converter", 1),
            ("ReplayGain", 2),
            ("Artwork Transfer", 3)
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_tab(idx))
            self.nav_buttons.append(btn)
            side_layout.addWidget(btn)

        side_layout.addStretch()

        root_layout.addWidget(sidebar)

        # Content Area
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentFrame")

        self.tab_metadata = MetadataEditorTab()
        self.tab_converter = BaselineConverterTab()
        self.tab_replaygain = ReplayGainTab()
        self.tab_transfer = ArtTransferTab()

        self.content_stack.addWidget(self.tab_metadata)
        self.content_stack.addWidget(self.tab_converter)
        self.content_stack.addWidget(self.tab_replaygain)
        self.content_stack.addWidget(self.tab_transfer)

        root_layout.addWidget(self.content_stack)

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
