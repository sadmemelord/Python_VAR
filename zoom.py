import sys
import cv2
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.video_cap = cv2.VideoCapture("C:\\Users\\Admin\\Desktop\\Alberto\\PTZ_10.avi")  # Replace with your video file path
        self.video_fps = int(self.video_cap.get(cv2.CAP_PROP_FPS)) if self.video_cap.get(cv2.CAP_PROP_FPS) > 0 else 30
        self.zoom_factor = 1.0
        self.cumulative_wheel_delta = 0

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)

        if self.video_fps > 0:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(1000 // self.video_fps)

        # Periodically apply the cumulative wheel delta
        self.zoom_timer = QTimer(self)
        self.zoom_timer.timeout.connect(self.apply_zoom)
        self.zoom_timer.start(50)  # Adjust the interval for smoother zooming

    def update_frame(self):
        ret, frame = self.video_cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = frame.shape

            # Resize the frame based on the current zoom factor
            zoomed_frame = cv2.resize(frame, (int(w * self.zoom_factor), int(h * self.zoom_factor)))

            image = QImage(zoomed_frame, zoomed_frame.shape[1], zoomed_frame.shape[0], zoomed_frame.shape[1] * c, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.video_label.setPixmap(pixmap)

    def wheelEvent(self, event):
        # Accumulate wheel delta for smoother zooming
        self.cumulative_wheel_delta += event.angleDelta().y()

    def apply_zoom(self):
        zoom_speed = 0.001  # Adjust the speed of zooming

        # Apply cumulative wheel delta to the zoom factor
        self.zoom_factor *= (1 + zoom_speed * self.cumulative_wheel_delta)

        # Reset cumulative wheel delta
        self.cumulative_wheel_delta = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
