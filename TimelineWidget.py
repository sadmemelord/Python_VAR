from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene

class TimelineWidget(QWidget):
    cursor_positions_changed = Signal(int, int)

    def __init__(self, range_max, parent=None):
        super().__init__(parent)

        self.range_max = range_max
        self.head_position = 0
        self.tail_position = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.timeline_view = QGraphicsView()
        self.timeline_scene = QGraphicsScene()
        self.timeline_view.setScene(self.timeline_scene)

        layout.addWidget(self.timeline_view)

        self.setStyleSheet("background-color: #333;")


    def update_timeline(self):
        self.timeline_scene.clear()

        # Draw the timeline
        pen = QPen(Qt.SolidLine)
        pen.setColor(Qt.white)

        timeline_height = 30
        timeline_rect = QRectF(0, 0, self.width(), timeline_height)
        self.timeline_scene.addRect(timeline_rect, pen)

        # Draw the head cursor
        head_rect = QRectF(self.head_position, 0, 2, timeline_height)
        self.timeline_scene.addRect(head_rect, pen)

        # Draw the tail cursor
        tail_rect = QRectF(self.tail_position, 0, 2, timeline_height)
        self.timeline_scene.addRect(tail_rect, pen)

        self.timeline_view.setSceneRect(self.timeline_scene.itemsBoundingRect())

    def set_cursor_positions(self, head_position, tail_position):
        if head_position != self.head_position or tail_position != self.tail_position:
            self.head_position = head_position
            self.tail_position = tail_position
            self.update_timeline()
            self.cursor_positions_changed.emit(self.head_position, self.tail_position)
