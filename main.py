from PySide6.QtWidgets import QApplication
from videoPlayer import VideoPlayer

if __name__ == "__main__":
    app = QApplication([])
    player = VideoPlayer()
    app.exec_()
