"""
Custom UI Widgets for Audio Kit
- FileDropZone: Clean drag & drop zone accepting audio files and directories
- ArtworkDropZone: Drag & drop zone specifically for image/cover art files
- StatBadge: Minimalist pill badge showing tag info / status
"""

import os
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage
from core.engine import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS, scan_audio_files

class FileDropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, title="Drag & Drop Audio Files or Folders", subtitle="Supports FLAC, MP3, M4A, OGG, Opus", parent=None):
        super().__init__(parent)
        self.setProperty("class", "DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        self.icon_label = QLabel("🎵")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 28px; background: transparent;")

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F8FAFC; background: transparent;")

        self.sub_label = QLabel(subtitle)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 11px; color: #64748B; background: transparent;")

        browse_btn = QPushButton("Browse Files")
        browse_btn.setProperty("class", "SecondaryBtn")
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self._browse_files)

        btn_container = QHBoxLayout()
        btn_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_container.addWidget(browse_btn)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.sub_label)
        layout.addLayout(btn_container)

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
            # Expand directories to audio files
            resolved = scan_audio_files(paths)
            if resolved:
                self.files_dropped.emit(resolved)
        event.acceptProposedAction()


class ArtworkDropZone(QFrame):
    """
    Cover art display that allows clicking or dragging an image to replace artwork.
    """
    artwork_changed = pyqtSignal(bytes)  # Emits raw image bytes

    def __init__(self, size=220, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setProperty("class", "DropZone")
        self.setAcceptDrops(True)
        self.current_bytes = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(4, 4, 4, 4)

        self.preview_label = QLabel("No Cover\n(Drop Image Here)")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #64748B; font-size: 12px; background: transparent;")
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
        self.preview_label.setText("No Cover\n(Drop Image Here)")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            f, _ = QFileDialog.getOpenFileName(
                self, "Select Cover Artwork", "",
                "Image Files (*.jpg *.jpeg *.png *.webp *.bmp)"
            )
            if f:
                with open(f, 'rb') as fp:
                    data = fp.read()
                self.set_artwork(data)
                self.artwork_changed.emit(data)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in SUPPORTED_IMAGE_EXTENSIONS:
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
        event.acceptProposedAction()
