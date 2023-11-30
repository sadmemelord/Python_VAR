from PySide6.QtWidgets import QApplication
from VideoPlayer import VideoPlayer

if __name__ == "__main__":
    app = QApplication([])
    window = VideoPlayer()
    app.exec_()
