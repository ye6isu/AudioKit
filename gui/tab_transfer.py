"""
Tab 4: Artwork Transfer Engine
Dedicated dual-zone cloner to inherit cover art from one file/image and batch-apply it across tracks.
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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        head_layout = QVBoxLayout()
        head_layout.setSpacing(4)
        title = QLabel("ARTWORK CLONER & TRANSFER")
        title.setProperty("class", "ViewHeader")
        desc = QLabel("Inherit cover art from an image or music track and batch-apply to target albums")
        desc.setProperty("class", "ViewSubheader")
        head_layout.addWidget(title)
        head_layout.addWidget(desc)
        layout.addLayout(head_layout)

        # Split Zones
        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(16)

        # Source Card
        source_card = QFrame()
        source_card.setProperty("class", "Card")
        source_card.setFixedWidth(280)
        s_layout = QVBoxLayout(source_card)
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.setContentsMargins(18, 18, 18, 18)
        s_layout.setSpacing(10)

        s_title = QLabel("SOURCE ARTWORK")
        s_title.setStyleSheet("font-weight: 700; font-size: 10px; letter-spacing: 0.8px; color: #8A8A93;")
        s_desc = QLabel("Drop song with cover, or image file")
        s_desc.setStyleSheet("color: #666670; font-size: 11px;")

        self.source_drop = ArtworkDropZone(size=180)
        self.source_drop.artwork_changed.connect(self._on_source_art_loaded)

        s_btn_row = QHBoxLayout()
        s_btn_row.setSpacing(6)
        btn_img = QPushButton("Image...")
        btn_img.setProperty("class", "GhostBtn")
        btn_img.clicked.connect(self.source_drop.choose_from_image)

        btn_song = QPushButton("Song...")
        btn_song.setProperty("class", "GhostBtn")
        btn_song.clicked.connect(self.source_drop.choose_from_audio)

        s_btn_row.addWidget(btn_img)
        s_btn_row.addWidget(btn_song)

        s_layout.addWidget(s_title)
        s_layout.addWidget(s_desc)
        s_layout.addWidget(self.source_drop)
        s_layout.addLayout(s_btn_row)
        zones_layout.addWidget(source_card)

        # Targets Card
        target_card = QFrame()
        target_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(target_card)
        t_layout.setContentsMargins(18, 18, 18, 18)
        t_layout.setSpacing(10)

        t_title = QLabel("DESTINATION TRACKS")
        t_title.setStyleSheet("font-weight: 700; font-size: 10px; letter-spacing: 0.8px; color: #8A8A93;")
        t_desc = QLabel("Drop files or folders to inherit source artwork")
        t_desc.setStyleSheet("color: #666670; font-size: 11px;")

        self.target_drop = FileDropZone(title="DROP DESTINATION TRACKS OR FOLDERS", subtitle="Will receive source cover in Baseline JPEG format")
        self.target_drop.files_dropped.connect(self._on_targets_dropped)

        self.target_table = QTableWidget()
        self.target_table.setColumnCount(2)
        self.target_table.setHorizontalHeaderLabels(["DESTINATION FILE", "STATUS"])
        self.target_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.target_table.setColumnWidth(1, 140)

        t_layout.addWidget(t_title)
        t_layout.addWidget(t_desc)
        t_layout.addWidget(self.target_drop)
        t_layout.addWidget(self.target_table)
        zones_layout.addWidget(target_card, stretch=2)

        layout.addLayout(zones_layout)

        # Bottom Transfer Button
        self.transfer_btn = QPushButton("TRANSFER & EMBED ARTWORK")
        self.transfer_btn.setProperty("class", "PrimaryBtn")
        self.transfer_btn.setEnabled(False)
        self.transfer_btn.clicked.connect(self.perform_transfer)
        layout.addWidget(self.transfer_btn)

    def _on_source_art_loaded(self, img_bytes):
        self.source_art_bytes = img_bytes
        self._check_ready()

    def _on_targets_dropped(self, files):
        self.target_files = files
        self.target_table.setRowCount(len(files))
        for row, p in enumerate(files):
            fname = os.path.basename(p)
            self.target_table.setItem(row, 0, QTableWidgetItem(fname))
            item_status = QTableWidgetItem("QUEUED")
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
                status_item = QTableWidgetItem("COMPLIANT ✓")
            else:
                status_item = QTableWidgetItem("FAILED ✗")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.target_table.setItem(row, 1, status_item)

        QMessageBox.information(
            self, "Transfer Finished",
            f"Transferred and standardized cover artwork across {applied} of {len(self.target_files)} tracks."
        )
