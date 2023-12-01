from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPixmap, QImage
import numpy as np

class VideoRendererThread(QThread):
    update_signal = Signal(np.ndarray, int)

    def __init__(self, video_label, parent=None):
        super().__init__(parent)
        self.video_label = video_label

    def run(self):
        self.update_signal.connect(self.video_label_update)

    def video_label_update(self, display_frame: np.ndarray):
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        q_image = q_image.scaled(self.video_label.width(),self.video_label.height(), 
                                 Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation )

        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)


