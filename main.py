from PySide6.QtWidgets import QApplication
from VideoPlayer import VideoPlayer
from VideoPlayer2 import VideoPlayer2


if __name__ == "__main__":
    app = QApplication([])
    window = VideoPlayer2()
    #player = VideoPlayer()
    app.exec_()
