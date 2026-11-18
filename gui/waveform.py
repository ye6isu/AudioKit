"""
WaveformTimeline Widget for Audio Kit
Renders an interactive audio waveform with draggable Start and End range handles,
active selection highlight, and live playback playhead.
"""

import numpy as np
import soundfile as sf
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent

class WaveformTimeline(QWidget):
    rangeChanged = pyqtSignal(float, float) # start_sec, end_sec
    seekRequested = pyqtSignal(float)       # pos_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.duration_sec = 0.0
        self.start_sec = 0.0
        self.end_sec = 0.0
        self.current_pos_sec = 0.0
        self.peaks = [] # Normalized peak amplitudes (0.0 to 1.0)

        # Dragging state
        self.dragging_handle = None # 'start', 'end', or 'seek'
        self.handle_width = 10

    def load_audio(self, file_path):
        try:
            info = sf.info(file_path)
            self.duration_sec = float(info.duration)
            self.start_sec = 0.0
            self.end_sec = self.duration_sec
            self.current_pos_sec = 0.0

            # Downsample to ~350 waveform bins for smooth visual rendering
            data, _ = sf.read(file_path, dtype='float32')
            if len(data.shape) > 1:
                mono = np.mean(data, axis=1)
            else:
                mono = data

            num_bins = 350
            chunks = np.array_split(mono, num_bins)
            raw_peaks = [float(np.max(np.abs(c))) if len(c) > 0 else 0.0 for c in chunks]
            max_p = max(raw_peaks) if max(raw_peaks) > 0 else 1.0
            self.peaks = [p / max_p for p in raw_peaks]

            self.rangeChanged.emit(self.start_sec, self.end_sec)
            self.update()
        except Exception:
            self.duration_sec = 0.0
            self.peaks = []
            self.update()

    def set_range(self, start, end):
        self.start_sec = max(0.0, min(start, self.duration_sec))
        self.end_sec = max(self.start_sec, min(end, self.duration_sec))
        self.update()

    def set_playhead(self, pos_sec):
        self.current_pos_sec = pos_sec
        self.update()

    def _sec_to_x(self, sec):
        if self.duration_sec <= 0:
            return 0
        w = self.width() - (self.handle_width * 2)
        return self.handle_width + int((sec / self.duration_sec) * w)

    def _x_to_sec(self, x):
        if self.duration_sec <= 0:
            return 0.0
        w = self.width() - (self.handle_width * 2)
        clamped_x = max(self.handle_width, min(x, self.width() - self.handle_width))
        ratio = (clamped_x - self.handle_width) / max(1, w)
        return ratio * self.duration_sec

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        mid_y = h / 2.0

        # Background base
        painter.fillRect(0, 0, w, h, QColor("#121215"))

        if not self.peaks or self.duration_sec <= 0:
            painter.setPen(QColor("#4C4C55"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No waveform loaded")
            return

        start_x = self._sec_to_x(self.start_sec)
        end_x = self._sec_to_x(self.end_sec)
        play_x = self._sec_to_x(self.current_pos_sec)

        # Inactive outside dims
        painter.fillRect(0, 0, start_x, h, QColor(0, 0, 0, 140))
        painter.fillRect(end_x, 0, w - end_x, h, QColor(0, 0, 0, 140))

        # Selected Active Region Highlight
        painter.fillRect(start_x, 0, end_x - start_x, h, QColor(255, 85, 0, 28))

        # Draw Waveform Bars
        num_peaks = len(self.peaks)
        content_w = w - (self.handle_width * 2)
        bar_w = max(1.5, content_w / num_peaks - 1)

        for i, peak in enumerate(self.peaks):
            bx = self.handle_width + (i * (content_w / num_peaks))
            bar_h = max(2.0, peak * (h - 26))

            # Color active vs inactive bars
            if start_x <= bx <= end_x:
                color = QColor("#FF5500") # TE Signal Orange
            else:
                color = QColor("#383842") # Dimmed inactive

            painter.fillRect(QRectF(bx, mid_y - (bar_h / 2.0), bar_w, bar_h), color)

        # Draw Start Handle (Left Orange Bracket)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FF5500")))
        painter.drawRoundedRect(QRectF(start_x - 4, 0, 8, h), 4, 4)

        # Draw End Handle (Right Orange Bracket)
        painter.drawRoundedRect(QRectF(end_x - 4, 0, 8, h), 4, 4)

        # Center line in handles for grip cue
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawLine(int(start_x), 15, int(start_x), h - 15)
        painter.drawLine(int(end_x), 15, int(end_x), h - 15)

        # Draw Playhead cursor (Thin White needle)
        if start_x <= play_x <= end_x:
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawLine(int(play_x), 0, int(play_x), h)

    def mousePressEvent(self, event: QMouseEvent):
        if self.duration_sec <= 0:
            return
        x = event.pos().x()
        start_x = self._sec_to_x(self.start_sec)
        end_x = self._sec_to_x(self.end_sec)

        # Check if clicking on or near start handle
        if abs(x - start_x) <= 12:
            self.dragging_handle = 'start'
        elif abs(x - end_x) <= 12:
            self.dragging_handle = 'end'
        else:
            # Click inside timeline requests playhead seek
            self.dragging_handle = 'seek'
            click_sec = self._x_to_sec(x)
            self.seekRequested.emit(click_sec)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.duration_sec <= 0:
            return
        x = event.pos().x()
        start_x = self._sec_to_x(self.start_sec)
        end_x = self._sec_to_x(self.end_sec)

        if not self.dragging_handle:
            # Update cursor on hover over handles
            if abs(x - start_x) <= 12 or abs(x - end_x) <= 12:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            return

        new_sec = self._x_to_sec(x)

        if self.dragging_handle == 'start':
            self.start_sec = max(0.0, min(new_sec, self.end_sec - 0.2))
            self.rangeChanged.emit(self.start_sec, self.end_sec)
            self.update()
        elif self.dragging_handle == 'end':
            self.end_sec = max(self.start_sec + 0.2, min(new_sec, self.duration_sec))
            self.rangeChanged.emit(self.start_sec, self.end_sec)
            self.update()
        elif self.dragging_handle == 'seek':
            self.seekRequested.emit(new_sec)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging_handle = None
