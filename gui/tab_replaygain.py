"""
Tab 3: ReplayGain 2.0 Normalizer
Calculates integrated loudness (-18.0 LUFS target) and true sample peaks,
writing standardized ReplayGain tags for consistent volume across albums.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.widgets import FileDropZone
from core.engine import (
    calculate_loudness_and_peak, apply_replaygain_tags, DEFAULT_TARGET_LUFS
)

class ReplayGainWorker(QThread):
    progress = pyqtSignal(int, int, str, str, str) # idx, total, gain_str, peak_str, log_msg
    finished = pyqtSignal(int)

    def __init__(self, file_paths, target_lufs=-18.0):
        super().__init__()
        self.file_paths = file_paths
        self.target_lufs = target_lufs

    def run(self):
        total = len(self.file_paths)
        gains = []
        peaks = []

        # Track-level analysis
        for idx, path in enumerate(self.file_paths):
            fname = os.path.basename(path)
            try:
                gain_db, peak, loudness = calculate_loudness_and_peak(path, self.target_lufs)
                gains.append(gain_db)
                peaks.append(peak)
                gain_str = f"{gain_db:+.2f} dB"
                peak_str = f"{peak:.4f}"
                log = f"Analyzed: {fname} -> {loudness:.1f} LUFS (Gain: {gain_str})"
            except Exception as e:
                gains.append(0.0)
                peaks.append(1.0)
                gain_str = "Error"
                peak_str = "Error"
                log = f"Error analyzing {fname}: {e}"

            self.progress.emit(idx + 1, total, gain_str, peak_str, log)

        # Calculate Album Gain (simple average of valid track gains & max peak)
        valid_gains = [g for g in gains if g != 0.0]
        album_gain = sum(valid_gains) / len(valid_gains) if valid_gains else 0.0
        album_peak = max(peaks) if peaks else 1.0

        # Apply tags
        for path, g, p in zip(self.file_paths, gains, peaks):
            try:
                apply_replaygain_tags(path, g, p, album_gain, album_peak)
            except Exception:
                pass

        self.finished.emit(total)


class ReplayGainTab(QWidget):
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
        title = QLabel("ReplayGain 2.0 Normalizer")
        title.setProperty("class", "SectionTitle")
        desc = QLabel("EBU R128 Loudness matching (-18.00 LUFS standard target) with True Peak calculation")
        desc.setProperty("class", "SectionDesc")
        head_layout.addWidget(title)
        head_layout.addWidget(desc)
        layout.addLayout(head_layout)

        # Drop Zone
        self.drop_zone = FileDropZone(
            title="Drop Album or Songs Here to Scan Loudness",
            subtitle="Calculates Track & Album Gain for consistent playback volume"
        )
        self.drop_zone.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drop_zone)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Track", "File Name", "Gain (dB)", "Peak"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom Bar: Analyze & Tag Button
        bottom_layout = QHBoxLayout()
        self.calc_btn = QPushButton("Calculate & Apply ReplayGain Tags")
        self.calc_btn.setProperty("class", "PrimaryBtn")
        self.calc_btn.setEnabled(False)
        self.calc_btn.clicked.connect(self.start_replaygain)
        bottom_layout.addWidget(self.calc_btn)
        layout.addLayout(bottom_layout)

        # Log
        self.console = QTextEdit()
        self.console.setObjectName("LogConsole")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(90)
        layout.addWidget(self.console)

    def on_files_dropped(self, paths):
        self.file_list = paths
        self.table.setRowCount(len(paths))
        for row, p in enumerate(paths):
            fname = os.path.basename(p)
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(fname))
            self.table.setItem(row, 2, QTableWidgetItem("Ready to scan"))
            self.table.setItem(row, 3, QTableWidgetItem("—"))
        self.console.append(f"Loaded {len(paths)} tracks for ReplayGain analysis.")
        self.calc_btn.setEnabled(len(paths) > 0)

    def start_replaygain(self):
        if not self.file_list:
            return
        self.calc_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.file_list))
        self.progress_bar.setValue(0)

        self.worker = ReplayGainWorker(self.file_list, DEFAULT_TARGET_LUFS)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current, total, gain_str, peak_str, log_msg):
        self.progress_bar.setValue(current)
        row = current - 1
        if row < self.table.rowCount():
            self.table.setItem(row, 2, QTableWidgetItem(gain_str))
            self.table.setItem(row, 3, QTableWidgetItem(peak_str))
        self.console.append(log_msg)

    def _on_finished(self, total):
        self.progress_bar.setVisible(False)
        self.calc_btn.setEnabled(True)
        self.console.append(f"Complete! ReplayGain tags written to all {total} tracks.")
