"""
Tab 2: Baseline JPEG Converter (De-cluttered)
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.widgets import FileDropZone
from core.engine import (
    extract_artwork, inspect_cover_art,
    convert_to_baseline_jpeg, set_artwork, deduplicate_tags
)
from mutagen.flac import FLAC

class ConverterWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        total = len(self.file_paths)
        fixed_count = 0

        for idx, path in enumerate(self.file_paths):
            fname = os.path.basename(path)
            try:
                raw_art, mime = extract_artwork(path)
                if raw_art:
                    info = inspect_cover_art(raw_art)
                    if info['needs_fix'] or info['is_progressive']:
                        set_artwork(path, raw_art, standardize_baseline=True)
                        fixed_count += 1
                        msg = f"Fixed: {fname}"
                    else:
                        msg = f"OK: {fname}"
                else:
                    msg = f"No cover: {fname}"

                ext = os.path.splitext(path)[1].lower()
                if ext == '.flac':
                    flac_obj = FLAC(path)
                    if deduplicate_tags(flac_obj.tags):
                        flac_obj.save()

            except Exception as e:
                msg = f"Error {fname}: {e}"

            self.progress.emit(idx + 1, total, msg)

        self.finished.emit(fixed_count, total)


class BaselineConverterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("Baseline Converter")
        title.setProperty("class", "ViewHeader")
        layout.addWidget(title)

        # Drop Zone
        self.drop_zone = FileDropZone(title="Drop audio files or folders here")
        self.drop_zone.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drop_zone)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Format", "Cover Specs", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 100)
        layout.addWidget(self.table)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action Bar
        bottom_layout = QHBoxLayout()
        self.fix_btn = QPushButton("Convert All to Baseline")
        self.fix_btn.setProperty("class", "PrimaryBtn")
        self.fix_btn.setEnabled(False)
        self.fix_btn.clicked.connect(self.start_fix)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.fix_btn)
        layout.addLayout(bottom_layout)

        # Log
        self.console = QTextEdit()
        self.console.setObjectName("LogConsole")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(85)
        layout.addWidget(self.console)

    def on_files_dropped(self, paths):
        self.file_list = paths
        self.table.setRowCount(len(paths))
        needs_fix_count = 0

        for row, p in enumerate(paths):
            fname = os.path.basename(p)
            ext = os.path.splitext(p)[1].upper().replace('.', '')
            self.table.setItem(row, 0, QTableWidgetItem(fname))
            self.table.setItem(row, 1, QTableWidgetItem(ext))

            raw_art, _ = extract_artwork(p)
            if raw_art:
                info = inspect_cover_art(raw_art)
                art_status = f"{info['format']} {info['size'][0]}x{info['size'][1]}"
                if info['is_progressive']:
                    art_status += " (Progressive)"
                if info['needs_fix']:
                    status_str = "Needs Fix"
                    needs_fix_count += 1
                else:
                    status_str = "Compliant"
            else:
                art_status = "No Cover"
                status_str = "—"

            item_spec = QTableWidgetItem(art_status)
            item_status = QTableWidgetItem(status_str)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_spec)
            self.table.setItem(row, 3, item_status)

        self.console.append(f"Loaded {len(paths)} tracks ({needs_fix_count} need baseline fix).")
        self.fix_btn.setEnabled(len(paths) > 0)

    def start_fix(self):
        if not self.file_list:
            return
        self.fix_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.file_list))
        self.progress_bar.setValue(0)

        self.worker = ConverterWorker(self.file_list)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current, total, msg):
        self.progress_bar.setValue(current)
        self.console.append(msg)

    def _on_finished(self, fixed_count, total_count):
        self.progress_bar.setVisible(False)
        self.fix_btn.setEnabled(True)
        self.console.append(f"Finished. Standardized {fixed_count} of {total_count} files.")
        self.on_files_dropped(self.file_list)
