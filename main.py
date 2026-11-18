"""
Audio Kit - Complete Desktop Audio Studio
Tabs:
1. Library & Tags (Metadata, Cover Manager, Baseline Fixer)
2. Loudness (EBU R128, ReplayGain -18 LUFS)
3. Trimmer (Sample-accurate waveform range cutter with live playback)
4. Converter (Batch audio format transcoder: FLAC, MP3, WAV, OGG)
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QComboBox, QSlider, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from gui.waveform import WaveformTimeline

from core.engine import (
    scan_audio_files, read_audio_metadata, save_audio_metadata,
    extract_artwork, set_artwork, trim_audio_file, convert_audio_format,
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

/* Input Fields & Spinboxes */
QLineEdit, QDoubleSpinBox, QComboBox {
    background-color: #0E0E10;
    border: 1px solid #26262E;
    border-radius: 5px;
    padding: 6px 10px;
    color: #FFFFFF;
    font-size: 12px;
    height: 18px;
}

QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #FF5500;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
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

/* Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #202026;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #FF5500;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 1px solid #FF5500;
    width: 12px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 6px;
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


class BatchConvertThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int)

    def __init__(self, file_paths, target_ext, output_dir=None):
        super().__init__()
        self.file_paths = file_paths
        self.target_ext = target_ext
        self.output_dir = output_dir

    def run(self):
        total = len(self.file_paths)
        for idx, p in enumerate(self.file_paths):
            fname = os.path.basename(p)
            try:
                out = convert_audio_format(p, self.target_ext, self.output_dir)
                msg = f"Converted: {fname} -> {os.path.basename(out)}"
            except Exception as e:
                msg = f"Failed {fname}: {e}"
            self.progress.emit(idx + 1, total, msg)
        self.finished.emit(total)


class AudioKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Kit")
        self.resize(1040, 700)
        self.setMinimumSize(900, 580)

        # App Icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.file_list = []
        self.current_meta = None
        self.copied_art_bytes = None
        self.loudness_worker = None
        self.convert_worker = None

        # Audio Player for Trimmer
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self._on_player_pos_changed)
        self.player.durationChanged.connect(self._on_player_duration_changed)

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
        h_layout.setSpacing(12)

        title = QLabel("Audio Kit")
        title.setObjectName("BrandTitle")
        h_layout.addWidget(title)

        # Tabs: Library, Loudness, Trimmer, Converter
        self.nav_tabs = []
        tab_names = ["Library", "Loudness", "Trimmer", "Converter"]
        for idx, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setProperty("class", "TabBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._set_active_view(i))
            self.nav_tabs.append(btn)
            h_layout.addWidget(btn)

        h_layout.addStretch()

        # Batch Fix Cover button
        self.btn_batch_baseline = QPushButton("Fix All Covers to Baseline")
        self.btn_batch_baseline.setObjectName("BatchFixBtn")
        self.btn_batch_baseline.setToolTip("Auto-converts all loaded tracks' artwork to standard Baseline JPEG for player compatibility")
        self.btn_batch_baseline.clicked.connect(self.batch_standardize_covers)
        h_layout.addWidget(self.btn_batch_baseline)

        main_layout.addWidget(header)

        # 2. Universal Drop Bar
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

        # 3. Middle Content Views
        self.content_stack = QFrame()
        stack_layout = QVBoxLayout(self.content_stack)
        stack_layout.setContentsMargins(16, 0, 16, 0)
        stack_layout.setSpacing(0)

        # --- View 0: Library Table ---
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(5)
        self.library_table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Album", "Cover"])
        self.library_table.verticalHeader().setVisible(False)
        self.library_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.library_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.library_table.setColumnWidth(0, 56)
        self.library_table.setColumnWidth(2, 160)
        self.library_table.setColumnWidth(4, 100)
        self.library_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.library_table.itemSelectionChanged.connect(self._on_track_selected)
        stack_layout.addWidget(self.library_table)

        # --- View 1: Loudness View ---
        self.loudness_container = QWidget()
        l_layout = QVBoxLayout(self.loudness_container)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(8)

        self.loudness_table = QTableWidget()
        self.loudness_table.setColumnCount(4)
        self.loudness_table.setHorizontalHeaderLabels(["#", "File Name", "Gain (dB)", "True Peak"])
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

        # --- View 2: Trimmer View ---
        self.trimmer_container = QWidget()
        t_layout = QVBoxLayout(self.trimmer_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(12)

        self.trim_file_label = QLabel("Select a track in the library to trim")
        self.trim_file_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #FFFFFF;")
        t_layout.addWidget(self.trim_file_label)

        # Interactive Waveform with drag handles
        self.waveform = WaveformTimeline()
        self.waveform.rangeChanged.connect(self._on_waveform_range_changed)
        self.waveform.seekRequested.connect(self._on_waveform_seek)
        t_layout.addWidget(self.waveform)

        # Controls & Spinboxes
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(14)

        self.btn_play_pause = QPushButton("Play")
        self.btn_play_pause.setProperty("class", "GhostBtn")
        self.btn_play_pause.setFixedWidth(80)
        self.btn_play_pause.clicked.connect(self._toggle_playback)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #8C8C96; font-size: 11px;")

        ctrl_row.addWidget(self.btn_play_pause)
        ctrl_row.addWidget(self.time_label)
        ctrl_row.addStretch()

        # Start & End Spinboxes (synchronized with waveform handles)
        ctrl_row.addWidget(QLabel("Start:"))
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0.0, 9999.0)
        self.spin_start.setSingleStep(0.2)
        self.spin_start.setSuffix("s")
        self.spin_start.setFixedWidth(84)
        self.spin_start.valueChanged.connect(self._on_spin_changed)
        ctrl_row.addWidget(self.spin_start)

        ctrl_row.addWidget(QLabel("End:"))
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0.0, 9999.0)
        self.spin_end.setSingleStep(0.2)
        self.spin_end.setSuffix("s")
        self.spin_end.setFixedWidth(84)
        self.spin_end.valueChanged.connect(self._on_spin_changed)
        ctrl_row.addWidget(self.spin_end)

        self.btn_trim_save = QPushButton("Save Trimmed Audio")
        self.btn_trim_save.setProperty("class", "PrimaryBtn")
        self.btn_trim_save.clicked.connect(self._execute_trim)
        ctrl_row.addWidget(self.btn_trim_save)

        t_layout.addLayout(ctrl_row)

        self.trim_log = QTextEdit()
        self.trim_log.setObjectName("ConsoleView")
        self.trim_log.setReadOnly(True)
        self.trim_log.setFixedHeight(120)
        t_layout.addWidget(self.trim_log)
        stack_layout.addWidget(self.trimmer_container)

        # --- View 3: Converter View ---
        self.converter_container = QWidget()
        c_layout = QVBoxLayout(self.converter_container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(10)

        self.convert_table = QTableWidget()
        self.convert_table.setColumnCount(3)
        self.convert_table.setHorizontalHeaderLabels(["#", "File Name", "Status"])
        self.convert_table.verticalHeader().setVisible(False)
        self.convert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.convert_table.setColumnWidth(0, 48)
        self.convert_table.setColumnWidth(2, 140)
        c_layout.addWidget(self.convert_table)

        self.convert_bar = QProgressBar()
        self.convert_bar.setVisible(False)
        c_layout.addWidget(self.convert_bar)

        c_act_row = QHBoxLayout()
        c_act_row.setSpacing(12)

        c_act_row.addWidget(QLabel("Target Format:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["FLAC (.flac)", "MP3 (.mp3)", "WAV (.wav)", "OGG (.ogg)"])
        self.combo_format.setFixedWidth(140)
        c_act_row.addWidget(self.combo_format)
        c_act_row.addStretch()

        self.btn_start_convert = QPushButton("Convert All Files")
        self.btn_start_convert.setProperty("class", "PrimaryBtn")
        self.btn_start_convert.clicked.connect(self._start_batch_convert)
        c_act_row.addWidget(self.btn_start_convert)
        c_layout.addLayout(c_act_row)

        self.convert_log = QTextEdit()
        self.convert_log.setObjectName("ConsoleView")
        self.convert_log.setReadOnly(True)
        self.convert_log.setFixedHeight(85)
        c_layout.addWidget(self.convert_log)
        stack_layout.addWidget(self.converter_container)

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
        self.inp_track.setFixedWidth(80)
        self.inp_year = QLineEdit()
        self.inp_year.setPlaceholderText("Year")
        self.inp_year.setFixedWidth(100)
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
        for i, tab_btn in enumerate(self.nav_tabs):
            tab_btn.setChecked(i == index)

        self.library_table.setVisible(index == 0)
        self.loudness_container.setVisible(index == 1)
        self.trimmer_container.setVisible(index == 2)
        self.converter_container.setVisible(index == 3)
        self.footer.setVisible(index == 0)

        # Stop audio playback if navigating away from trimmer
        if index != 2 and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setText("Play")

    # --- Loading & Drop Handlers ---
    def _browse_audio(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.flac *.mp3 *.m4a *.mp4 *.ogg *.opus *.wav *.aiff)"
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
        self.convert_table.setRowCount(len(paths))

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

            # Converter table
            item_cnum = QTableWidgetItem(str(row + 1))
            item_cnum.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.convert_table.setItem(row, 0, item_cnum)
            self.convert_table.setItem(row, 1, QTableWidgetItem(fname))
            item_cstat = QTableWidgetItem("Ready")
            item_cstat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.convert_table.setItem(row, 2, item_cstat)

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

            # Update trimmer target
            dur = self.current_meta.get('duration_sec', 0.0)
            self.trim_file_label.setText(f"Trimming: {os.path.basename(path)} ({dur:.1f}s)")
            self.spin_start.setValue(0.0)
            self.spin_end.setMaximum(dur)
            self.spin_end.setValue(dur)
            self.waveform.load_audio(path)
            self.player.setSource(QUrl.fromLocalFile(path))

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

    # --- Trimmer Methods ---
    def _on_waveform_range_changed(self, start, end):
        self.spin_start.blockSignals(True)
        self.spin_end.blockSignals(True)
        self.spin_start.setValue(start)
        self.spin_end.setValue(end)
        self.spin_start.blockSignals(False)
        self.spin_end.blockSignals(False)

    def _on_spin_changed(self):
        s = self.spin_start.value()
        e = self.spin_end.value()
        if e > s:
            self.waveform.set_range(s, e)

    def _on_waveform_seek(self, sec):
        self.player.setPosition(int(sec * 1000))
        self.waveform.set_playhead(sec)

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setText("Play")
        else:
            # Play starting from start handle if current position is outside range
            cur_sec = self.player.position() / 1000
            if cur_sec < self.spin_start.value() or cur_sec >= self.spin_end.value():
                self.player.setPosition(int(self.spin_start.value() * 1000))
            self.player.play()
            self.btn_play_pause.setText("Pause")

    def _on_player_pos_changed(self, pos_ms):
        dur_ms = self.player.duration()
        cur_s = pos_ms / 1000
        tot_s = dur_ms / 1000 if dur_ms > 0 else 0
        self.time_label.setText(f"{int(cur_s//60)}:{int(cur_s%60):02d} / {int(tot_s//60)}:{int(tot_s%60):02d}")
        self.waveform.set_playhead(cur_s)

        # Loop or stop if reaching end of selection range
        end_s = self.spin_end.value()
        if end_s > 0 and cur_s >= end_s and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setText("Play")

    def _on_player_duration_changed(self, dur_ms):
        tot_s = dur_ms / 1000
        self.spin_end.setMaximum(tot_s)

    def _seek_player(self, val):
        pass

    def _execute_trim(self):
        if not self.current_meta:
            QMessageBox.warning(self, "No Track", "Select a track to trim.")
            return

        source = self.current_meta['filepath']
        s_sec = self.spin_start.value()
        e_sec = self.spin_end.value()

        if e_sec <= s_sec:
            QMessageBox.warning(self, "Invalid Range", "End time must be greater than start time.")
            return

        base, ext = os.path.splitext(source)
        dest_default = f"{base}_trimmed{ext}"
        dest, _ = QFileDialog.getSaveFileName(self, "Save Trimmed File", dest_default, f"Audio File (*{ext})")
        if dest:
            try:
                trim_audio_file(source, dest, s_sec, e_sec)
                self.trim_log.append(f"Trimmed successfully: {os.path.basename(dest)} ({s_sec:.1f}s -> {e_sec:.1f}s)")
                QMessageBox.information(self, "Trim Complete", f"Trimmed audio saved to {os.path.basename(dest)}")
            except Exception as ex:
                self.trim_log.append(f"Error trimming {os.path.basename(source)}: {ex}")
                QMessageBox.critical(self, "Error", str(ex))

    # --- Batch Converter Methods ---
    def _start_batch_convert(self):
        if not self.file_list:
            QMessageBox.warning(self, "No Files", "No audio files loaded.")
            return

        target_ext_str = self.combo_format.currentText()
        ext_map = {"FLAC (.flac)": ".flac", "MP3 (.mp3)": ".mp3", "WAV (.wav)": ".wav", "OGG (.ogg)": ".ogg"}
        target_ext = ext_map.get(target_ext_str, ".flac")

        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory (or Cancel to save alongside source)")
        out_dir = out_dir if out_dir else None

        self.btn_start_convert.setEnabled(False)
        self.convert_bar.setVisible(True)
        self.convert_bar.setMaximum(len(self.file_list))
        self.convert_bar.setValue(0)

        self.convert_worker = BatchConvertThread(self.file_list, target_ext, out_dir)
        self.convert_worker.progress.connect(self._on_convert_progress)
        self.convert_worker.finished.connect(self._on_convert_finished)
        self.convert_worker.start()

    def _on_convert_progress(self, current, total, msg):
        self.convert_bar.setValue(current)
        row = current - 1
        if row < self.convert_table.rowCount():
            item_done = QTableWidgetItem("Converted ✓")
            item_done.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.convert_table.setItem(row, 2, item_done)
        self.convert_log.append(msg)

    def _on_convert_finished(self, total):
        self.convert_bar.setVisible(False)
        self.btn_start_convert.setEnabled(True)
        self.convert_log.append(f">> Finished batch conversion for {total} files.")


def main():
    try:
        import ctypes
        myappid = 'yebisu.audiokit.desktop.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setStyleSheet(APP_QSS)
    win = AudioKitMainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
