"""
Tab 2: Walkman Cover Fixer (Baseline JPEG standardizer)
Scans files/folders, detects progressive JPEGs and incompatible artwork,
and converts them into Walkman-safe Baseline JPEG format.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.widgets import FileDropZone
from core.engine import (
    scan_audio_files, extract_artwork, inspect_cover_art,
    convert_to_baseline_jpeg, set_artwork, deduplicate_tags
)
from mutagen.flac import FLAC

class FixerWorker(QThread):
    progress = pyqtSignal(int, int, str) # current, total, log_message
    finished = pyqtSignal(int, int)      # fixed_count, total_count

    def __init__(self, file_paths, max_dim=None):
        super().__init__()
        self.file_paths = file_paths
        self.max_dim = max_dim

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
                        msg = f"✓ Fixed art -> Baseline JPEG: {fname}"
                    else:
                        msg = f"• Already Baseline JPEG: {fname}"
                else:
                    msg = f"- No artwork embedded: {fname}"

                # Deduplicate tags as well
                ext = os.path.splitext(path)[1].lower()
                if ext == '.flac':
                    flac_obj = FLAC(path)
                    if deduplicate_tags(flac_obj.tags):
                        flac_obj.save()
                        msg += " (deduplicated tags)"

            except Exception as e:
                msg = f"✗ Error processing {fname}: {e}"

            self.progress.emit(idx + 1, total, msg)

        self.finished.emit(fixed_count, total)


class WalkmanFixerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        head_layout = QVBoxLayout()
        head_layout.setSpacing(4)
        title = QLabel("Walkman & DAP Cover Fixer")
        title.setProperty("class", "SectionTitle")
        desc = QLabel("Standardize artwork to Baseline RGB JPEG (Quality 95) for Sony Walkmans & legacy players")
        desc.setProperty("class", "SectionDesc")
        head_layout.addWidget(title)
        head_layout.addWidget(desc)
        layout.addLayout(head_layout)

        # Drop Zone
        self.drop_zone = FileDropZone(
            title="Drop Music Files or Folders to Inspect Compatibility",
            subtitle="Drop albums, FLACs, or MP3s to check artwork"
        )
        self.drop_zone.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drop_zone)

        # Table & Status
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Format", "Art Status", "Action Needed"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom Bar: Fix Button & Log console
        bottom_layout = QHBoxLayout()
        self.fix_btn = QPushButton("Standardize All Covers to Baseline JPEG")
        self.fix_btn.setProperty("class", "PrimaryBtn")
        self.fix_btn.setEnabled(False)
        self.fix_btn.clicked.connect(self.start_fix)
        bottom_layout.addWidget(self.fix_btn)
        layout.addLayout(bottom_layout)

        # Console
        self.console = QTextEdit()
        self.console.setObjectName("LogConsole")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(90)
        layout.addWidget(self.console)

    def on_files_dropped(self, paths):
        self.file_list = paths
        self.table.setRowCount(len(paths))
        needs_fix_count = 0

        for row, p in enumerate(paths):
            fname = os.path.basename(p)
            ext = os.path.splitext(p)[1].upper()
            self.table.setItem(row, 0, QTableWidgetItem(fname))
            self.table.setItem(row, 1, QTableWidgetItem(ext))

            raw_art, _ = extract_artwork(p)
            if raw_art:
                info = inspect_cover_art(raw_art)
                art_status = f"{info['format']} {info['size'][0]}x{info['size'][1]}"
                if info['is_progressive']:
                    art_status += " (Progressive)"
                if info['needs_fix']:
                    action = "⚠️ Needs Fix"
                    needs_fix_count += 1
                else:
                    action = "✓ Compatible"
            else:
                art_status = "No Cover"
                action = "—"

            self.table.setItem(row, 2, QTableWidgetItem(art_status))
            self.table.setItem(row, 3, QTableWidgetItem(action))

        self.console.append(f"Loaded {len(paths)} tracks. Found {needs_fix_count} track(s) needing Walkman baseline fix.")
        self.fix_btn.setEnabled(len(paths) > 0)

    def start_fix(self):
        if not self.file_list:
            return
        self.fix_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.file_list))
        self.progress_bar.setValue(0)

        self.worker = FixerWorker(self.file_list)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current, total, msg):
        self.progress_bar.setValue(current)
        self.console.append(msg)

    def _on_finished(self, fixed_count, total_count):
        self.progress_bar.setVisible(False)
        self.fix_btn.setEnabled(True)
        self.console.append(f"Completed! Fixed artwork for {fixed_count}/{total_count} tracks.")
        # Refresh table
        self.on_files_dropped(self.file_list)
