"""
Tab 1: Metadata & Artwork Editor (De-cluttered, clean Apple-like aesthetic)
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from gui.widgets import FileDropZone, ArtworkDropZone
from core.engine import (
    read_audio_metadata, save_audio_metadata, set_artwork, remove_artwork
)

class MetadataEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []
        self.current_meta = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("Metadata & Artwork")
        title.setProperty("class", "ViewHeader")
        layout.addWidget(title)

        # Drop Zone
        self.drop_zone = FileDropZone(title="Drop audio files or folders here")
        self.drop_zone.files_dropped.connect(self.load_files)
        layout.addWidget(self.drop_zone)

        # Content Split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        # Left Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Cover"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 80)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        content_layout.addWidget(self.table, stretch=3)

        # Right Inspector Card
        self.inspector_card = QFrame()
        self.inspector_card.setProperty("class", "Card")
        self.inspector_card.setFixedWidth(300)
        card_layout = QVBoxLayout(self.inspector_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        # Cover
        self.art_zone = ArtworkDropZone(size=140)
        self.art_zone.artwork_changed.connect(self._on_art_dropped)
        card_layout.addWidget(self.art_zone, alignment=Qt.AlignmentFlag.AlignCenter)

        # Art action buttons
        art_btn_row = QHBoxLayout()
        art_btn_row.setSpacing(6)
        choose_img_btn = QPushButton("From Image")
        choose_img_btn.setProperty("class", "GhostBtn")
        choose_img_btn.clicked.connect(self.art_zone.choose_from_image)

        choose_music_btn = QPushButton("From Song")
        choose_music_btn.setProperty("class", "GhostBtn")
        choose_music_btn.clicked.connect(self.art_zone.choose_from_audio)

        art_btn_row.addWidget(choose_img_btn)
        art_btn_row.addWidget(choose_music_btn)
        card_layout.addLayout(art_btn_row)

        self.art_status_label = QLabel("No cover")
        self.art_status_label.setStyleSheet("color: #727280; font-size: 11px;")
        self.art_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.art_status_label)

        # Form fields
        self.fields = {}
        form_keys = [
            ('Title', 'title'),
            ('Artist', 'artist'),
            ('Album', 'album'),
            ('Track', 'track'),
            ('Year', 'year'),
            ('Genre', 'genre')
        ]
        for label_text, key in form_keys:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(55)
            lbl.setStyleSheet("color: #8C8C9A; font-size: 11px;")
            edit = QLineEdit()
            self.fields[key] = edit
            row.addWidget(lbl)
            row.addWidget(edit)
            card_layout.addLayout(row)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        self.remove_art_btn = QPushButton("Remove Art")
        self.remove_art_btn.setProperty("class", "SecondaryBtn")
        self.remove_art_btn.clicked.connect(self.remove_current_art)

        self.save_btn = QPushButton("Save")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.clicked.connect(self.save_current_tags)

        btn_layout.addWidget(self.remove_art_btn)
        btn_layout.addWidget(self.save_btn)
        card_layout.addLayout(btn_layout)

        content_layout.addWidget(self.inspector_card, stretch=2)
        layout.addLayout(content_layout)

    def load_files(self, paths):
        self.file_list = paths
        self.table.setRowCount(len(paths))
        for row, path in enumerate(paths):
            meta = read_audio_metadata(path)
            self.table.setItem(row, 0, QTableWidgetItem(meta.get('track') or str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(meta.get('title') or os.path.basename(path)))
            self.table.setItem(row, 2, QTableWidgetItem(meta.get('artist') or "—"))
            
            art_text = "OK" if meta.get('has_art') else "—"
            if meta.get('art_info') and meta['art_info']['needs_fix']:
                art_text = "Fix"
            art_item = QTableWidgetItem(art_text)
            art_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, art_item)

        if paths:
            self.table.selectRow(0)

    def _on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self.file_list):
            path = self.file_list[row]
            self.current_meta = read_audio_metadata(path)
            for k, edit in self.fields.items():
                edit.setText(self.current_meta.get(k, ''))

            if self.current_meta['has_art']:
                self.art_zone.set_artwork(self.current_meta['art_bytes'])
                info = self.current_meta['art_info']
                status_text = f"{info['format']} {info['size'][0]}x{info['size'][1]}"
                if info['is_progressive']:
                    status_text += " (Progressive)"
                elif info['needs_fix']:
                    status_text += " (Non-Baseline)"
                else:
                    status_text += " (Baseline)"
                self.art_status_label.setText(status_text)
            else:
                self.art_zone.set_artwork(None)
                self.art_status_label.setText("No cover")

    def _on_art_dropped(self, img_bytes):
        if not self.current_meta:
            return
        path = self.current_meta['filepath']
        success = set_artwork(path, img_bytes, standardize_baseline=True)
        if success:
            self.art_status_label.setText("Cover Updated (Baseline)")
            self._update_table_row_art(self.table.currentRow(), True)

    def save_current_tags(self):
        if not self.current_meta:
            return
        path = self.current_meta['filepath']
        updates = {k: edit.text().strip() for k, edit in self.fields.items()}
        success = save_audio_metadata(path, updates)
        if success:
            row = self.table.currentRow()
            if row >= 0:
                self.table.setItem(row, 0, QTableWidgetItem(updates.get('track', '')))
                self.table.setItem(row, 1, QTableWidgetItem(updates.get('title', '')))
                self.table.setItem(row, 2, QTableWidgetItem(updates.get('artist', '')))
            QMessageBox.information(self, "Saved", f"Metadata saved for {os.path.basename(path)}")

    def remove_current_art(self):
        if not self.current_meta:
            return
        path = self.current_meta['filepath']
        if remove_artwork(path):
            self.art_zone.set_artwork(None)
            self.art_status_label.setText("No cover")
            self._update_table_row_art(self.table.currentRow(), False)

    def _update_table_row_art(self, row, has_art):
        if row >= 0 and row < self.table.rowCount():
            item = QTableWidgetItem("OK" if has_art else "—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item)
