from PySide6.QtCore import QThread, Signal
import cv2

class VideoWriterThread(QThread):
    finished = Signal()

    def __init__(self, buffer: list, width: int, height: int, fps: int, filename: str, fourcc: cv2.VideoWriter_fourcc, parent=None):
        super().__init__()
        self.buffer = buffer
        self.filename = filename
        self.fourcc = fourcc
        self.fps = fps
        self.width = width
        self.height = height

    def run(self):
        writer = cv2.VideoWriter(self.filename, self.fourcc, self.fps, (self.width, self.height))
        try:
            for frame in self.buffer:
                writer.write(frame)
        except:
            cv2.Error("Couldn't write file to disk")

        writer.release()
        self.finished.emit()
