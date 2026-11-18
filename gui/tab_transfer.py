"""
Tab 4: Artwork Transfer (De-cluttered)
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.widgets import FileDropZone, ArtworkDropZone
from core.engine import extract_artwork, set_artwork

class ArtTransferTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_art_bytes = None
        self.target_files = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("Artwork Transfer")
        title.setProperty("class", "ViewHeader")
        layout.addWidget(title)

        # Split Zones
        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(14)

        # Source Card
        source_card = QFrame()
        source_card.setProperty("class", "Card")
        source_card.setFixedWidth(240)
        s_layout = QVBoxLayout(source_card)
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.setContentsMargins(16, 16, 16, 16)
        s_layout.setSpacing(10)

        s_title = QLabel("Source Artwork")
        s_title.setStyleSheet("font-weight: 600; font-size: 11px; color: #8A8A93;")

        self.source_drop = ArtworkDropZone(size=140)
        self.source_drop.artwork_changed.connect(self._on_source_art_loaded)

        s_btn_row = QHBoxLayout()
        s_btn_row.setSpacing(6)
        btn_img = QPushButton("Image")
        btn_img.setProperty("class", "GhostBtn")
        btn_img.clicked.connect(self.source_drop.choose_from_image)

        btn_song = QPushButton("Song")
        btn_song.setProperty("class", "GhostBtn")
        btn_song.clicked.connect(self.source_drop.choose_from_audio)

        s_btn_row.addWidget(btn_img)
        s_btn_row.addWidget(btn_song)

        s_layout.addWidget(s_title)
        s_layout.addWidget(self.source_drop)
        s_layout.addLayout(s_btn_row)
        zones_layout.addWidget(source_card)

        # Targets Card
        target_card = QFrame()
        target_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(target_card)
        t_layout.setContentsMargins(16, 16, 16, 16)
        t_layout.setSpacing(10)

        t_title = QLabel("Destination Tracks")
        t_title.setStyleSheet("font-weight: 600; font-size: 11px; color: #8A8A93;")

        self.target_drop = FileDropZone(title="Drop destination files or folders")
        self.target_drop.files_dropped.connect(self._on_targets_dropped)

        self.target_table = QTableWidget()
        self.target_table.setColumnCount(2)
        self.target_table.setHorizontalHeaderLabels(["File", "Status"])
        self.target_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.target_table.setColumnWidth(1, 120)

        t_layout.addWidget(t_title)
        t_layout.addWidget(self.target_drop)
        t_layout.addWidget(self.target_table)
        zones_layout.addWidget(target_card, stretch=2)

        layout.addLayout(zones_layout)

        # Bottom Transfer Button
        bottom_row = QHBoxLayout()
        self.transfer_btn = QPushButton("Transfer Artwork")
        self.transfer_btn.setProperty("class", "PrimaryBtn")
        self.transfer_btn.setEnabled(False)
        self.transfer_btn.clicked.connect(self.perform_transfer)
        bottom_row.addStretch()
        bottom_row.addWidget(self.transfer_btn)
        layout.addLayout(bottom_row)

    def _on_source_art_loaded(self, img_bytes):
        self.source_art_bytes = img_bytes
        self._check_ready()

    def _on_targets_dropped(self, files):
        self.target_files = files
        self.target_table.setRowCount(len(files))
        for row, p in enumerate(files):
            fname = os.path.basename(p)
            self.target_table.setItem(row, 0, QTableWidgetItem(fname))
            item_status = QTableWidgetItem("Ready")
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.target_table.setItem(row, 1, item_status)
        self._check_ready()

    def _check_ready(self):
        ready = (self.source_art_bytes is not None) and (len(self.target_files) > 0)
        self.transfer_btn.setEnabled(ready)

    def perform_transfer(self):
        if not self.source_art_bytes or not self.target_files:
            return

        applied = 0
        for row, path in enumerate(self.target_files):
            success = set_artwork(path, self.source_art_bytes, standardize_baseline=True)
            if success:
                applied += 1
                status_item = QTableWidgetItem("Updated ✓")
            else:
                status_item = QTableWidgetItem("Failed ✗")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.target_table.setItem(row, 1, status_item)

        QMessageBox.information(
            self, "Complete",
            f"Transferred artwork to {applied} of {len(self.target_files)} tracks."
        )
