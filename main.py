"""
Audio Kit Main Application Window
Refined Teenage Engineering & Apple utility aesthetic:
Matte chassis, tactile navigation sidebar, mechanical keycap buttons.
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
        self.setWindowTitle("AUDIO KIT")
        self.resize(1120, 740)
        self.setMinimumSize(960, 620)

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
        side_layout.setContentsMargins(18, 28, 18, 28)
        side_layout.setSpacing(10)

        # Branding Header
        brand_row = QHBoxLayout()
        title_label = QLabel("AUDIO KIT")
        title_label.setObjectName("AppBrand")
        brand_tag = QLabel("STUDIO")
        brand_tag.setObjectName("BrandTag")
        brand_row.addWidget(title_label)
        brand_row.addWidget(brand_tag)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        sub_label = QLabel("AUDIO UTILITY SYSTEM")
        sub_label.setStyleSheet("font-size: 9px; font-weight: 700; color: #585862; letter-spacing: 1px; margin-bottom: 16px;")
        side_layout.addWidget(sub_label)

        # Navigation Items
        self.nav_buttons = []
        nav_items = [
            ("TAG & ART EDITOR", 0),
            ("BASELINE CONVERTER", 1),
            ("REPLAYGAIN ENGINE", 2),
            ("ARTWORK TRANSFER", 3)
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_tab(idx))
            self.nav_buttons.append(btn)
            side_layout.addWidget(btn)

        side_layout.addStretch()

        # Machine Specs Footer
        footer_box = QVBoxLayout()
        footer_box.setSpacing(2)
        f_ver = QLabel("SYS VER 1.0.0")
        f_ver.setStyleSheet("color: #4C4C54; font-size: 9px; font-weight: 700; letter-spacing: 0.8px;")
        f_spec = QLabel("EBU R128 • BASELINE JPEG")
        f_spec.setStyleSheet("color: #3C3C44; font-size: 8px; font-weight: 600; letter-spacing: 0.5px;")
        footer_box.addWidget(f_ver)
        footer_box.addWidget(f_spec)
        side_layout.addLayout(footer_box)

        root_layout.addWidget(sidebar)

        # --- Content Area ---
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
