import sys
from PySide6.QtCore import QFile, Signal
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtUiTools import QUiLoader

class DialogSettings(QDialog):
    updateSettings = Signal(int, int, str, str)

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

        self.dialog_window.output_path_button.clicked.connect(self.select_output_path)

    def select_output_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly

        # Open the file dialog to select a folder
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder', options=options)

        if folder_path:
            print(f'Selected Folder: {folder_path}')
            self.dialog_window.output_path_edit.setText(folder_path + "\\")
        else:
            self.dialog_window.output_path_edit.setText("output\\")

    def closeEvent(self, event):
        number_of_cameras = self.dialog_window.number_of_cameras_spinbox.value()
        buffer_size = self.dialog_window.buffer_size_spinbox.value()
        encoding = self.dialog_window.encoding_combobox.currentText()
        output_path = self.dialog_window.output_path_edit.text()

        self.updateSettings.emit(number_of_cameras, buffer_size, encoding, output_path)

        event.accept()  # Accept the event to allow the dialog to close
