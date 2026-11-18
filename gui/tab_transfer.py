"""
Tab 4: Album Art Transfer / Cloner
Allows dragging a source track or image file to inherit cover artwork,
and applying it across all selected target songs or folders in one click.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.widgets import FileDropZone, ArtworkDropZone
from core.engine import extract_artwork, set_artwork, scan_audio_files

class ArtTransferTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_art_bytes = None
        self.target_files = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        head_layout = QVBoxLayout()
        head_layout.setSpacing(4)
        title = QLabel("Artwork Cloner & Transfer")
        title.setProperty("class", "SectionTitle")
        desc = QLabel("Inherit cover art from one file/image and batch-apply it to target songs or folders")
        desc.setProperty("class", "SectionDesc")
        head_layout.addWidget(title)
        head_layout.addWidget(desc)
        layout.addLayout(head_layout)

        # Split Zones (Source Left, Targets Right)
        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(16)

        # Source Card
        source_card = QFrame()
        source_card.setProperty("class", "Card")
        source_card.setFixedWidth(280)
        s_layout = QVBoxLayout(source_card)
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.setContentsMargins(16, 16, 16, 16)
        s_layout.setSpacing(10)

        s_title = QLabel("Source Artwork")
        s_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #F8FAFC;")
        s_desc = QLabel("Drop song with cover, or image file")
        s_desc.setStyleSheet("color: #64748B; font-size: 11px;")

        self.source_drop = ArtworkDropZone(size=200)
        self.source_drop.artwork_changed.connect(self._on_source_art_loaded)

        s_layout.addWidget(s_title)
        s_layout.addWidget(s_desc)
        s_layout.addWidget(self.source_drop)
        zones_layout.addWidget(source_card)

        # Targets Right
        target_card = QFrame()
        target_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(target_card)
        t_layout.setContentsMargins(16, 16, 16, 16)
        t_layout.setSpacing(10)

        t_title = QLabel("Target Audio Files")
        t_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #F8FAFC;")
        t_desc = QLabel("Drop destination tracks or folders to receive the artwork")
        t_desc.setStyleSheet("color: #64748B; font-size: 11px;")

        self.target_drop = FileDropZone(title="Drop Target Songs or Folders", subtitle="Files will inherit the source cover")
        self.target_drop.files_dropped.connect(self._on_targets_dropped)

        self.target_table = QTableWidget()
        self.target_table.setColumnCount(2)
        self.target_table.setHorizontalHeaderLabels(["Target File", "Status"])
        self.target_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        t_layout.addWidget(t_title)
        t_layout.addWidget(t_desc)
        t_layout.addWidget(self.target_drop)
        t_layout.addWidget(self.target_table)
        zones_layout.addWidget(target_card, stretch=2)

        layout.addLayout(zones_layout)

        # Bottom Transfer Button
        self.transfer_btn = QPushButton("Transfer & Apply Artwork to Target Files")
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
            self.target_table.setItem(row, 1, QTableWidgetItem("Ready"))
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
                self.target_table.setItem(row, 1, QTableWidgetItem("✓ Updated (Baseline)"))
            else:
                self.target_table.setItem(row, 1, QTableWidgetItem("✗ Failed"))

        QMessageBox.information(
            self, "Transfer Complete",
            f"Successfully applied Walkman-baseline cover art to {applied} out of {len(self.target_files)} target tracks!"
        )
