"""
Unified 2-View Desktop Application for Audio Kit
Refined based on real track visual review:
- Hidden ugly vertical header column (no duplicate row numbers)
- Generous track column width to avoid '10/...' truncation
- Clean button typography ('Library & Tags', 'Scan & Tag ReplayGain')
- Aligned table headers and input field heights
- Balanced bottom metadata tray
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QFileDialog, QMessageBox, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap

from core.engine import (
    scan_audio_files, read_audio_metadata, save_audio_metadata,
    extract_artwork, set_artwork,
    calculate_loudness_and_peak, apply_replaygain_tags, DEFAULT_TARGET_LUFS,
    SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS
)

APP_QSS = """
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #EDEDED;
    outline: none;
}

QMainWindow, QWidget#MainRoot {
    background-color: #0E0E10;
}

/* Header bar */
QFrame#TopHeader {
    background-color: #141417;
    border-bottom: 1px solid #222228;
}

QLabel#BrandTitle {
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.5px;
}

/* Tab toggle buttons */
QPushButton.TabBtn {
    background-color: transparent;
    color: #8C8C96;
    font-weight: 600;
    font-size: 12px;
    padding: 7px 16px;
    border-radius: 6px;
    border: none;
}

QPushButton.TabBtn:hover {
    color: #FFFFFF;
    background-color: #1F1F24;
}

QPushButton.TabBtn:checked {
    background-color: #26262E;
    color: #FF5500;
}

/* Header action button */
QPushButton#BatchFixBtn {
    background-color: #1A1A1F;
    color: #D4D4D8;
    font-size: 11px;
    font-weight: 600;
    border-radius: 6px;
    padding: 6px 14px;
    border: 1px solid #2B2B34;
}

QPushButton#BatchFixBtn:hover {
    background-color: #24242C;
    border-color: #383844;
    color: #FFFFFF;
}

/* Drop bar */
QFrame#DropBar {
    background-color: #131316;
    border: 1px dashed #282832;
    border-radius: 6px;
}

QFrame#DropBar:hover {
    border-color: #FF5500;
    background-color: #17171C;
}

/* Clean Tables */
QTableWidget {
    background-color: #121215;
    border: 1px solid #1F1F24;
    border-radius: 6px;
    gridline-color: #18181D;
    selection-background-color: #22222A;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0F0F12;
    color: #7A7A85;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #1F1F24;
    font-weight: 600;
    font-size: 11px;
}

/* Bottom Inspector Footer */
QFrame#FooterPanel {
    background-color: #141417;
    border-top: 1px solid #222228;
}

/* Artwork Thumbnail */
QFrame#CoverBox {
    background-color: #0E0E10;
    border: 1px solid #26262E;
    border-radius: 6px;
}

QFrame#CoverBox:hover {
    border-color: #FF5500;
}

/* Input Fields */
QLineEdit {
    background-color: #0E0E10;
    border: 1px solid #26262E;
    border-radius: 5px;
    padding: 6px 10px;
    color: #FFFFFF;
    font-size: 12px;
    height: 18px;
}

QLineEdit:focus {
    border-color: #FF5500;
}

/* Buttons */
QPushButton.PrimaryBtn {
    background-color: #FF5500;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    border-radius: 5px;
    padding: 7px 16px;
    border: none;
    min-height: 18px;
}

QPushButton.PrimaryBtn:hover {
    background-color: #E64D00;
}

QPushButton.PrimaryBtn:disabled {
    background-color: #1F1F24;
    color: #4C4C55;
}

QPushButton.GhostBtn {
    background-color: #1A1A1F;
    color: #A1A1AA;
    font-size: 11px;
    font-weight: 500;
    border-radius: 5px;
    padding: 6px 12px;
    border: 1px solid #282832;
}

QPushButton.GhostBtn:hover {
    background-color: #24242C;
    color: #FFFFFF;
}

/* Progress bar */
QProgressBar {
    background-color: #121215;
    border: 1px solid #222228;
    border-radius: 3px;
    height: 6px;
}

QProgressBar::chunk {
    background-color: #FF5500;
    border-radius: 2px;
}

/* Monospace Console */
QTextEdit#ConsoleView {
    background-color: #0A0A0C;
    border: 1px solid #1B1B20;
    border-radius: 6px;
    color: #8A8A96;
    font-family: Consolas, monospace;
    font-size: 11px;
    padding: 8px 12px;
}
"""

class LoudnessThread(QThread):
    progress = pyqtSignal(int, int, str, str, str)
    finished = pyqtSignal(int)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        total = len(self.file_paths)
        gains, peaks = [], []
        for idx, path in enumerate(self.file_paths):
            fname = os.path.basename(path)
            try:
                g, p, lufs = calculate_loudness_and_peak(path, DEFAULT_TARGET_LUFS)
                gains.append(g)
                peaks.append(p)
                log = f"{fname} -> {lufs:.1f} LUFS ({g:+.2f} dB)"
                self.progress.emit(idx + 1, total, f"{g:+.2f} dB", f"{p:.4f}", log)
            except Exception as e:
                gains.append(0.0)
                peaks.append(1.0)
                self.progress.emit(idx + 1, total, "Err", "Err", f"Error {fname}: {e}")

        valid = [x for x in gains if x != 0.0]
        alb_gain = sum(valid) / len(valid) if valid else 0.0
        alb_peak = max(peaks) if peaks else 1.0

        for path, g, p in zip(self.file_paths, gains, peaks):
            try:
                apply_replaygain_tags(path, g, p, alb_gain, alb_peak)
            except Exception:
                pass
        self.finished.emit(total)


class AudioKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Kit")
        self.resize(1040, 700)
        self.setMinimumSize(900, 580)

        self.file_list = []
        self.current_meta = None
        self.copied_art_bytes = None
        self.loudness_worker = None

        root = QWidget()
        root.setObjectName("MainRoot")
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Header Bar
        header = QFrame()
        header.setObjectName("TopHeader")
        header.setFixedHeight(52)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        h_layout.setSpacing(16)

        title = QLabel("Audio Kit")
        title.setObjectName("BrandTitle")
        h_layout.addWidget(title)

        # Tabs with explicit labels
        self.btn_tab_library = QPushButton("Library")
        self.btn_tab_library.setProperty("class", "TabBtn")
        self.btn_tab_library.setCheckable(True)
        self.btn_tab_library.setChecked(True)
        self.btn_tab_library.clicked.connect(lambda: self._set_active_view(0))

        self.btn_tab_loudness = QPushButton("Loudness")
        self.btn_tab_loudness.setProperty("class", "TabBtn")
        self.btn_tab_loudness.setCheckable(True)
        self.btn_tab_loudness.clicked.connect(lambda: self._set_active_view(1))

        h_layout.addWidget(self.btn_tab_library)
        h_layout.addWidget(self.btn_tab_loudness)
        h_layout.addStretch()

        # Batch Fix Cover button
        self.btn_batch_baseline = QPushButton("Fix All Covers to Baseline")
        self.btn_batch_baseline.setObjectName("BatchFixBtn")
        self.btn_batch_baseline.setToolTip("Auto-converts all loaded tracks' artwork to standard Baseline JPEG for player compatibility")
        self.btn_batch_baseline.clicked.connect(self.batch_standardize_covers)
        h_layout.addWidget(self.btn_batch_baseline)

        main_layout.addWidget(header)

        # 2. Drop Bar
        self.drop_bar = QFrame()
        self.drop_bar.setObjectName("DropBar")
        self.drop_bar.setFixedHeight(46)
        self.drop_bar.setAcceptDrops(True)
        self.drop_bar.dragEnterEvent = self._dropbar_drag_enter
        self.drop_bar.dropEvent = self._dropbar_drop

        db_layout = QHBoxLayout(self.drop_bar)
        db_layout.setContentsMargins(16, 0, 16, 0)
        self.drop_label = QLabel("Drag & drop audio files or folders here")
        self.drop_label.setStyleSheet("color: #7E7E8B; font-size: 12px; background: transparent;")
        btn_browse = QPushButton("Browse...")
        btn_browse.setProperty("class", "GhostBtn")
        btn_browse.clicked.connect(self._browse_audio)
        db_layout.addWidget(self.drop_label)
        db_layout.addStretch()
        db_layout.addWidget(btn_browse)

        drop_container = QWidget()
        dc_layout = QVBoxLayout(drop_container)
        dc_layout.setContentsMargins(16, 12, 16, 8)
        dc_layout.addWidget(self.drop_bar)
        main_layout.addWidget(drop_container)

        # 3. Middle Content (Stack: Library View vs Loudness View)
        self.content_stack = QFrame()
        stack_layout = QVBoxLayout(self.content_stack)
        stack_layout.setContentsMargins(16, 0, 16, 0)
        stack_layout.setSpacing(0)

        # --- View 0: Library Table ---
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(5)
        self.library_table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Album", "Cover"])
        # Hide ugly default row number vertical header
        self.library_table.verticalHeader().setVisible(False)
        self.library_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.library_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.library_table.setColumnWidth(0, 56) # Wide enough for '10/13'
        self.library_table.setColumnWidth(2, 160)
        self.library_table.setColumnWidth(4, 100)
        self.library_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.library_table.itemSelectionChanged.connect(self._on_track_selected)
        stack_layout.addWidget(self.library_table)

        # --- View 1: Loudness Table & Console ---
        self.loudness_container = QWidget()
        l_layout = QVBoxLayout(self.loudness_container)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(8)

        self.loudness_table = QTableWidget()
        self.loudness_table.setColumnCount(4)
        self.loudness_table.setHorizontalHeaderLabels(["#", "File Name", "Gain (dB)", "True Peak"])
        # Hide vertical header
        self.loudness_table.verticalHeader().setVisible(False)
        self.loudness_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.loudness_table.setColumnWidth(0, 48)
        self.loudness_table.setColumnWidth(2, 120)
        self.loudness_table.setColumnWidth(3, 120)
        l_layout.addWidget(self.loudness_table)

        self.loudness_bar = QProgressBar()
        self.loudness_bar.setVisible(False)
        l_layout.addWidget(self.loudness_bar)

        act_row = QHBoxLayout()
        act_row.setSpacing(12)
        self.loudness_console = QTextEdit()
        self.loudness_console.setObjectName("ConsoleView")
        self.loudness_console.setReadOnly(True)
        self.loudness_console.setFixedHeight(75)
        act_row.addWidget(self.loudness_console, stretch=3)

        self.btn_calc_loudness = QPushButton("Scan & Tag ReplayGain")
        self.btn_calc_loudness.setProperty("class", "PrimaryBtn")
        self.btn_calc_loudness.setFixedHeight(36)
        self.btn_calc_loudness.clicked.connect(self._start_loudness_scan)
        act_row.addWidget(self.btn_calc_loudness, stretch=1)
        l_layout.addLayout(act_row)

        stack_layout.addWidget(self.loudness_container)
        self.loudness_container.setVisible(False)

        main_layout.addWidget(self.content_stack, stretch=1)

        # 4. Bottom Horizontal Metadata & Art Bar
        self.footer = QFrame()
        self.footer.setObjectName("FooterPanel")
        self.footer.setFixedHeight(144)
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(18, 14, 18, 14)
        f_layout.setSpacing(16)

        # Cover Thumbnail Card
        self.cover_box = QFrame()
        self.cover_box.setObjectName("CoverBox")
        self.cover_box.setFixedSize(116, 116)
        self.cover_box.setAcceptDrops(True)
        self.cover_box.dragEnterEvent = self._cover_drag_enter
        self.cover_box.dropEvent = self._cover_drop

        cb_layout = QVBoxLayout(self.cover_box)
        cb_layout.setContentsMargins(4, 4, 4, 4)
        self.cover_preview = QLabel("No Cover\n(Drop File)")
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setStyleSheet("color: #6C6C78; font-size: 10px; background: transparent;")
        self.cover_preview.setScaledContents(True)
        cb_layout.addWidget(self.cover_preview)
        f_layout.addWidget(self.cover_box)

        # Cover Control Actions
        cover_actions = QVBoxLayout()
        cover_actions.setSpacing(6)
        cover_actions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_choose_art = QPushButton("Replace...")
        self.btn_choose_art.setProperty("class", "GhostBtn")
        self.btn_choose_art.clicked.connect(self._choose_cover_dialog)

        self.btn_copy_art = QPushButton("Copy Cover")
        self.btn_copy_art.setProperty("class", "GhostBtn")
        self.btn_copy_art.clicked.connect(self._copy_cover)

        self.btn_apply_all = QPushButton("Apply to All")
        self.btn_apply_all.setProperty("class", "GhostBtn")
        self.btn_apply_all.setToolTip("Applies this cover to all tracks currently in the library")
        self.btn_apply_all.clicked.connect(self._apply_cover_to_all)

        cover_actions.addWidget(self.btn_choose_art)
        cover_actions.addWidget(self.btn_copy_art)
        cover_actions.addWidget(self.btn_apply_all)
        f_layout.addLayout(cover_actions)

        # Metadata 2-row clean grid
        grid_col = QVBoxLayout()
        grid_col.setSpacing(10)

        # Row 1: Title, Artist, Album
        r1 = QHBoxLayout()
        r1.setSpacing(12)
        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("Title")
        self.inp_artist = QLineEdit()
        self.inp_artist.setPlaceholderText("Artist")
        self.inp_album = QLineEdit()
        self.inp_album.setPlaceholderText("Album")
        r1.addWidget(self.inp_title, stretch=3)
        r1.addWidget(self.inp_artist, stretch=2)
        r1.addWidget(self.inp_album, stretch=3)
        grid_col.addLayout(r1)

        # Row 2: Track, Year, Genre, Save Tags
        r2 = QHBoxLayout()
        r2.setSpacing(12)
        self.inp_track = QLineEdit()
        self.inp_track.setPlaceholderText("Track #")
        self.inp_track.setFixedWidth(80) # Clean width for fractions e.g. 10/13
        self.inp_year = QLineEdit()
        self.inp_year.setPlaceholderText("Year")
        self.inp_year.setFixedWidth(100) # Clean width for full dates e.g. 2019-05-31
        self.inp_genre = QLineEdit()
        self.inp_genre.setPlaceholderText("Genre")

        self.btn_save_tags = QPushButton("Save Tags")
        self.btn_save_tags.setProperty("class", "PrimaryBtn")
        self.btn_save_tags.setFixedWidth(110)
        self.btn_save_tags.clicked.connect(self._save_tags)

        r2.addWidget(self.inp_track)
        r2.addWidget(self.inp_year)
        r2.addWidget(self.inp_genre, stretch=2)
        r2.addWidget(self.btn_save_tags)
        grid_col.addLayout(r2)

        f_layout.addLayout(grid_col, stretch=1)
        main_layout.addWidget(self.footer)

        self._set_active_view(0)

    def _set_active_view(self, index):
        if index == 0:
            self.btn_tab_library.setChecked(True)
            self.btn_tab_loudness.setChecked(False)
            self.library_table.setVisible(True)
            self.loudness_container.setVisible(False)
            self.footer.setVisible(True)
        else:
            self.btn_tab_library.setChecked(False)
            self.btn_tab_loudness.setChecked(True)
            self.library_table.setVisible(False)
            self.loudness_container.setVisible(True)
            self.footer.setVisible(False)

    # --- Loading & Drop Handlers ---
    def _browse_audio(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.flac *.mp3 *.m4a *.mp4 *.ogg *.opus *.wav)"
        )
        if files:
            self.load_audio_files(files)

    def _dropbar_drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _dropbar_drop(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if os.path.exists(u.toLocalFile())]
        resolved = scan_audio_files(paths)
        if resolved:
            self.load_audio_files(resolved)

    def load_audio_files(self, paths):
        self.file_list = paths
        self.drop_label.setText(f"{len(paths)} track(s) loaded")
        self.library_table.setRowCount(len(paths))
        self.loudness_table.setRowCount(len(paths))

        for row, path in enumerate(paths):
            meta = read_audio_metadata(path)
            fname = os.path.basename(path)

            # Library table
            item_num = QTableWidgetItem(meta.get('track') or str(row + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.library_table.setItem(row, 0, item_num)
            self.library_table.setItem(row, 1, QTableWidgetItem(meta.get('title') or fname))
            self.library_table.setItem(row, 2, QTableWidgetItem(meta.get('artist') or "—"))
            self.library_table.setItem(row, 3, QTableWidgetItem(meta.get('album') or "—"))

            art_text = "Baseline"
            if not meta.get('has_art'):
                art_text = "—"
            elif meta.get('art_info') and meta['art_info']['needs_fix']:
                art_text = "⚠️ Fix"
            art_item = QTableWidgetItem(art_text)
            art_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.library_table.setItem(row, 4, art_item)

            # Loudness table
            item_lnum = QTableWidgetItem(str(row + 1))
            item_lnum.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loudness_table.setItem(row, 0, item_lnum)
            self.loudness_table.setItem(row, 1, QTableWidgetItem(fname))
            item_gain = QTableWidgetItem("Ready")
            item_gain.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loudness_table.setItem(row, 2, item_gain)
            item_peak = QTableWidgetItem("—")
            item_peak.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loudness_table.setItem(row, 3, item_peak)

        if paths:
            self.library_table.selectRow(0)

    def _on_track_selected(self):
        selected = self.library_table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        if row < len(self.file_list):
            path = self.file_list[row]
            self.current_meta = read_audio_metadata(path)
            self.inp_title.setText(self.current_meta.get('title', ''))
            self.inp_artist.setText(self.current_meta.get('artist', ''))
            self.inp_album.setText(self.current_meta.get('album', ''))
            self.inp_track.setText(self.current_meta.get('track', ''))
            self.inp_year.setText(self.current_meta.get('year', ''))
            self.inp_genre.setText(self.current_meta.get('genre', ''))

            if self.current_meta['has_art']:
                self._display_cover(self.current_meta['art_bytes'])
            else:
                self.cover_preview.setPixmap(QPixmap())
                self.cover_preview.setText("No Cover\n(Drop File)")

    def _display_cover(self, img_bytes):
        pix = QPixmap()
        pix.loadFromData(img_bytes)
        if not pix.isNull():
            self.cover_preview.setPixmap(pix.scaled(
                108, 108, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.cover_preview.setText("No Cover")

    # --- Cover Actions ---
    def _cover_drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _cover_drop(self, event: QDropEvent):
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            ext = os.path.splitext(p)[1].lower()
            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                with open(p, 'rb') as fp:
                    self._set_current_cover(fp.read())
                break
            elif ext in SUPPORTED_AUDIO_EXTENSIONS:
                raw_art, _ = extract_artwork(p)
                if raw_art:
                    self._set_current_cover(raw_art)
                    break

    def _choose_cover_dialog(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select Image or Song to Inherit Cover", "",
            "Files (*.jpg *.jpeg *.png *.webp *.flac *.mp3 *.m4a)"
        )
        if f:
            raw_art, _ = extract_artwork(f)
            if raw_art:
                self._set_current_cover(raw_art)

    def _set_current_cover(self, img_bytes):
        if not self.current_meta:
            return
        path = self.current_meta['filepath']
        if set_artwork(path, img_bytes, standardize_baseline=True):
            self._display_cover(img_bytes)
            art_item = QTableWidgetItem("Baseline")
            art_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.library_table.setItem(self.library_table.currentRow(), 4, art_item)

    def _copy_cover(self):
        if self.current_meta and self.current_meta['has_art']:
            self.copied_art_bytes = self.current_meta['art_bytes']
            QMessageBox.information(self, "Cover Copied", "Artwork copied! You can now click 'Apply to All' or select another track.")

    def _apply_cover_to_all(self):
        source_art = self.copied_art_bytes or (self.current_meta['art_bytes'] if self.current_meta else None)
        if not source_art or not self.file_list:
            QMessageBox.warning(self, "No Cover", "Select a track with artwork or copy artwork first.")
            return

        for row, path in enumerate(self.file_list):
            if set_artwork(path, source_art, standardize_baseline=True):
                art_item = QTableWidgetItem("Baseline")
                art_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.library_table.setItem(row, 4, art_item)

        QMessageBox.information(self, "Applied", f"Baseline cover art applied across all {len(self.file_list)} tracks!")

    def batch_standardize_covers(self):
        if not self.file_list:
            return
        fixed = 0
        for row, path in enumerate(self.file_list):
            raw, _ = extract_artwork(path)
            if raw:
                set_artwork(path, raw, standardize_baseline=True)
                art_item = QTableWidgetItem("Baseline")
                art_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.library_table.setItem(row, 4, art_item)
                fixed += 1
        QMessageBox.information(self, "Standardization Complete", f"Standardized {fixed} tracks to Baseline JPEG.")

    def _save_tags(self):
        if not self.current_meta:
            return
        path = self.current_meta['filepath']
        updates = {
            'title': self.inp_title.text().strip(),
            'artist': self.inp_artist.text().strip(),
            'album': self.inp_album.text().strip(),
            'track': self.inp_track.text().strip(),
            'year': self.inp_year.text().strip(),
            'genre': self.inp_genre.text().strip()
        }
        if save_audio_metadata(path, updates):
            row = self.library_table.currentRow()
            if row >= 0:
                item_t = QTableWidgetItem(updates['track'])
                item_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.library_table.setItem(row, 0, item_t)
                self.library_table.setItem(row, 1, QTableWidgetItem(updates['title']))
                self.library_table.setItem(row, 2, QTableWidgetItem(updates['artist']))
                self.library_table.setItem(row, 3, QTableWidgetItem(updates['album']))
            QMessageBox.information(self, "Saved", f"Metadata saved for {os.path.basename(path)}")

    # --- Loudness / ReplayGain Scan ---
    def _start_loudness_scan(self):
        if not self.file_list:
            return
        self.btn_calc_loudness.setEnabled(False)
        self.loudness_bar.setVisible(True)
        self.loudness_bar.setMaximum(len(self.file_list))
        self.loudness_bar.setValue(0)

        self.loudness_worker = LoudnessThread(self.file_list)
        self.loudness_worker.progress.connect(self._on_loudness_progress)
        self.loudness_worker.finished.connect(self._on_loudness_finished)
        self.loudness_worker.start()

    def _on_loudness_progress(self, current, total, gain_str, peak_str, log):
        self.loudness_bar.setValue(current)
        row = current - 1
        if row < self.loudness_table.rowCount():
            item_g = QTableWidgetItem(gain_str)
            item_g.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_p = QTableWidgetItem(peak_str)
            item_p.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loudness_table.setItem(row, 2, item_g)
            self.loudness_table.setItem(row, 3, item_p)
        self.loudness_console.append(log)

    def _on_loudness_finished(self, total):
        self.loudness_bar.setVisible(False)
        self.btn_calc_loudness.setEnabled(True)
        self.loudness_console.append(f">> Finished scanning and tagging {total} tracks.")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    win = AudioKitMainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
