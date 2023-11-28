import sys
from PySide6.QtCore import Qt, QTimer, Slot, Signal, QTimeLine
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QProgressBar, QSlider
import cv2
import numpy as np

from CircularBuffer import CircularBuffer
from WorkerThread import WorkerThread
from TimelineWidget import TimelineWidget

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.buffer_size = 500
        self.circular_buffer = CircularBuffer(self.buffer_size)
        self.worker_thread = WorkerThread(self.circular_buffer, self)

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.video_label = QLabel(self)
        self.head_slider = QSlider(orientation=Qt.Orientation.Horizontal)
        self.head_slider.setTracking(True)
        self.head_slider.setRange(0, self.buffer_size)
        self.head_slider.setSingleStep(1)
        self.tail_slider = QSlider(orientation=Qt.Orientation.Horizontal)
        self.tail_slider.setRange(0, self.buffer_size)
        self.tail_slider.setSingleStep(1)
        self.playback_button = QPushButton('Play from Beginning', self)
        self.resume_button = QPushButton('Play in Real-Time', self)

        self.timeline_widget = TimelineWidget(self.buffer_size)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.video_label)
        layout.addWidget(self.timeline_widget)
        layout.addWidget(self.head_slider)
        layout.addWidget(self.tail_slider)
        layout.addWidget(self.playback_button)
        layout.addWidget(self.resume_button)

        self.playback_button.clicked.connect(self.start_playback)
        self.resume_button.clicked.connect(self.resume_realtime)

        self.worker_thread.frame_processed.connect(self.update_frame)
        self.worker_thread.head_position_updated.connect(self.update_head_slider)
        self.worker_thread.tail_position_updated.connect(self.update_tail_slider)
        self.worker_thread.head_position_updated.connect(self.update_timeline_head)
        self.worker_thread.tail_position_updated.connect(self.update_timeline_tail)

        self.timeline_widget.cursor_positions_changed.connect(self.update_timeline_head)
        self.tail_slider.sliderPressed.connect(self.slider_is_pressed)
        self.tail_slider.sliderMoved.connect(self.slider_is_moved)
        self.tail_slider.sliderReleased.connect(self.slider_is_released)
        self.worker_thread.start()

        self.show()
    
    def update_timeline_head(self, position):
        tail_position = self.circular_buffer.get_tail_position()
        self.timeline_widget.set_cursor_positions(position, tail_position)

    def update_timeline_tail(self, position):
        head_position = self.circular_buffer.get_head_position()
        self.timeline_widget.set_cursor_positions(head_position, position)

        # Additionally, update the tail slider
        self.timeline_widget.cursor_positions_changed.emit(head_position, position)

    @Slot(bool)
    def slider_is_pressed(self):
        self.worker_thread.tail_position_updated.disconnect(self.update_tail_slider)

    @Slot(int)
    def slider_is_moved(self, slider_value):
        self.worker_thread.set_buffer_peeking(is_peeking=True, new_peek_position=slider_value)

    @Slot(int)
    def slider_is_released(self):
        self.worker_thread.set_buffer_peeking(is_peeking=False, new_peek_position=None)
        self.circular_buffer.set_tail_position(self.tail_slider.value())
        self.worker_thread.tail_position_updated.connect(self.update_tail_slider)
    
    @Slot(int)
    def update_tail_slider(self, position):
        self.tail_slider.setValue(position)

    @Slot(int)
    def update_head_slider(self, position):
        # Update progress bar based on head position           
        self.head_slider.setValue(position)

    def start_playback(self):
        position = 0  # Set the playback position to the beginning
        try:
            self.circular_buffer.set_tail_position(position)
        except ValueError as e:
            print(f"Error setting playback position: {e}")

    def resume_realtime(self):
        self.circular_buffer.set_tail_position(self.circular_buffer.get_head_position())

    def update_frame(self, display_frame):
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)

        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)
