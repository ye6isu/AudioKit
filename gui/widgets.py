"""
Custom Clean UI Components for Audio Kit
"""

import os
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from core.engine import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS, scan_audio_files, extract_artwork

class FileDropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, title="Drop audio files or folders here", parent=None):
        super().__init__(parent)
        self.setProperty("class", "DropZone")
        self.setAcceptDrops(True)
        self.setFixedHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(12)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #E2E2E8; background: transparent;")

        browse_btn = QPushButton("Browse")
        browse_btn.setProperty("class", "GhostBtn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_files)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(browse_btn)

    def _browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.flac *.mp3 *.m4a *.mp4 *.ogg *.opus *.wav)"
        )
        if files:
            self.files_dropped.emit(files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.exists(local_path):
                paths.append(local_path)
        if paths:
            resolved = scan_audio_files(paths)
            if resolved:
                self.files_dropped.emit(resolved)
        event.acceptProposedAction()


class ArtworkDropZone(QFrame):
    artwork_changed = pyqtSignal(bytes)

    def __init__(self, size=150, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setProperty("class", "DropZone")
        self.setAcceptDrops(True)
        self.current_bytes = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(4, 4, 4, 4)

        self.preview_label = QLabel("Drop Cover Here\n(Image or Song)")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #6C6C78; font-size: 11px; font-weight: 500; background: transparent;")
        self.preview_label.setScaledContents(True)

        layout.addWidget(self.preview_label)

    def set_artwork(self, img_bytes):
        self.current_bytes = img_bytes
        if img_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(
                    self.width() - 8, self.height() - 8,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                return
        self.preview_label.setText("Drop Cover Here\n(Image or Song)")

    def choose_from_image(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Image Files (*.jpg *.jpeg *.png *.webp *.bmp *.tiff)"
        )
        if f:
            with open(f, 'rb') as fp:
                data = fp.read()
            self.set_artwork(data)
            self.artwork_changed.emit(data)

    def choose_from_audio(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.flac *.mp3 *.m4a *.mp4 *.ogg)"
        )
        if f:
            raw_art, _ = extract_artwork(f)
            if raw_art:
                self.set_artwork(raw_art)
                self.artwork_changed.emit(raw_art)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in SUPPORTED_IMAGE_EXTENSIONS or ext in SUPPORTED_AUDIO_EXTENSIONS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            ext = os.path.splitext(p)[1].lower()
            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                with open(p, 'rb') as fp:
                    data = fp.read()
                self.set_artwork(data)
                self.artwork_changed.emit(data)
                break
            elif ext in SUPPORTED_AUDIO_EXTENSIONS:
                raw_art, _ = extract_artwork(p)
                if raw_art:
                    self.set_artwork(raw_art)
                    self.artwork_changed.emit(raw_art)
                    break
        event.acceptProposedAction()
