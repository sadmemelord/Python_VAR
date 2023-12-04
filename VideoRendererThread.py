from PySide6.QtCore import QThread, Signal, Qt, QMutex, QMutexLocker, Slot
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QLabel
import numpy as np
import time
class VideoRendererThread(QThread):
    update_signal = Signal(np.ndarray, int)

    def __init__(self, video_label: QLabel, parent=None):
        super().__init__(parent)
        self.video_label = video_label
        self.mutex = QMutex()

    def run(self):
        self.update_signal.connect(self.video_label_update)

    @Slot(np.ndarray)
    def video_label_update(self, display_frame: np.ndarray):
        with QMutexLocker(self.mutex):

            height, width, channel = display_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
            q_image = q_image.scaled(self.video_label.width(),self.video_label.height(), 
                                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            pixmap = QPixmap.fromImage(q_image)
            self.video_label.setPixmap(pixmap)

    def switch_label_position(self, new_video_label: QLabel):
        self.video_label = new_video_label