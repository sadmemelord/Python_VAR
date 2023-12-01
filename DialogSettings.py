import sys
from PySide6.QtCore import QFile, Signal
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtUiTools import QUiLoader

class DialogSettings(QDialog):
    updateSettings = Signal(int, int, str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Settings')
        self.setFixedSize(300, 200)
        self.setModal(True)

        ui_file_path = QFile("VAR_System_ui\DialogSettings.ui")
        loader = QUiLoader()
        self.dialog_window = loader.load(ui_file_path)

        layout = QVBoxLayout()
        layout.addWidget(self.dialog_window)
        self.setLayout(layout)

        self.layout().setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, event):
        number_of_cameras = self.dialog_window.number_of_cameras_spinbox.value()
        buffer_size = self.dialog_window.buffer_size_spinbox.value()
        encoding = self.dialog_window.encoding_combobox.currentText()

        self.updateSettings.emit(number_of_cameras, buffer_size, encoding)

        event.accept()  # Accept the event to allow the dialog to close
