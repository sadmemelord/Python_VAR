from PySide6.QtCore import Qt, Slot, QMutex, QFile, QCoreApplication, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QMainWindow
import numpy as np

from CircularBuffer import CircularBuffer
from WorkerThread import WorkerThread

# Set required attributes before creating QGuiApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        #Loading the Main Window and its components from the .ui file
        ui_file_path = QFile("VAR_System_ui\MainWindow.ui")
        loader = QUiLoader()
        self.main_window = loader.load(ui_file_path)

        # Member variables
        self.buffer_size = 500
        self.circular_buffer = CircularBuffer(self.buffer_size)
        self.worker_thread = WorkerThread(buffer=self.circular_buffer, 
                                          capture_index=0, 
                                          parent=self.main_window)

        # Mutex for thread sync
        self.mutex = QMutex()

        # Function used to connect signals and start threads
        self.prepare_application()


    def prepare_application(self):
        '''Setting UI parameters. Connecting signals and slots. Showing the MainWindow.
        '''

        self.main_window.playback_slider.setRange(0, self.buffer_size)
        self.main_window.write_slider.setRange(0, self.buffer_size)

        self.worker_thread.display_frame.connect(self.update_frame)
        self.main_window.start_button.clicked.connect(self.start)
        self.main_window.realtime_button.clicked.connect(self.resume_realtime)
        self.main_window.playback_button.clicked.connect(self.restart_playback)
        self.main_window.save_buffer_button.clicked.connect(self.save_video_buffer)
        
        self.worker_thread.tail_position_updated.connect(self.update_playback_cursor_position)
        self.worker_thread.head_position_updated.connect(self.update_write_cursor_position)
        self.main_window.playback_slider.sliderPressed.connect(self.playback_cursor_pressed)
        self.main_window.playback_slider.sliderMoved.connect(self.playback_cursor_dragged)
        self.main_window.playback_slider.sliderReleased.connect(self.playback_cursor_released)

        self.main_window.actionSettings.triggered.connect(print("OPENING SETTINGS DIALOG"))
                
        self.setWindowTitle("VAR System Test")
        self.setCentralWidget(self.main_window)
        self.show()
    
    def restart_playback(self):
        '''Set the tail position to the beginning of the buffer'''
        self.mutex.lock()
        self.worker_thread.set_buffer_playback(True)
        self.mutex.unlock()
    
    def start(self):
        self.main_window.realtime_button.setEnabled(True)
        self.main_window.playback_button.setEnabled(True)
        self.main_window.save_buffer_button.setEnabled(True)
        self.main_window.start_button.setEnabled(False)
        self.worker_thread.start()
        
    @Slot(bool)
    def playback_cursor_pressed(self):
        '''When the playback cursor is pressed the thread stops updating the cursor position'''
        self.mutex.lock()
        self.worker_thread.tail_position_updated.disconnect(self.update_playback_cursor_position)
        self.mutex.unlock()

    @Slot(int)
    def playback_cursor_dragged(self, slider_value: int):
        '''When the playback cursor is dragged the thread starts peeking at the buffer in the selected position

            Arguments:
            -slider_value (int): The slider value is passed through a signal and determines the index to peek at
        '''
        self.mutex.lock()
        self.worker_thread.set_buffer_peeking(is_peeking=True, new_peek_position=slider_value)
        self.mutex.unlock()

    @Slot(int)
    def playback_cursor_released(self):
        '''When the playback cursor is released the thread stops peeking at the buffer and resumes playback from the selected position'''
        self.mutex.lock()
        self.worker_thread.set_buffer_peeking(is_peeking=False, new_peek_position=None)
        self.circular_buffer.set_tail_position(self.main_window.playback_slider.value())
        self.worker_thread.tail_position_updated.connect(self.update_playback_cursor_position)
        self.mutex.unlock()

    def resume_realtime(self):
        '''Set the tail position to the head position to resume the real-time playback'''
        self.mutex.lock()
        self.worker_thread.set_buffer_playback(False)
        self.mutex.unlock()
    
    @Slot(int)
    def update_playback_cursor_position(self, position:int):
        '''The playback cursor is connected to the tail pointer of the buffer. Its position is updated
            through a signal emitted by the WorkerThread.'''
        self.main_window.playback_slider.setValue(position)
    
    @Slot(int)
    def update_write_cursor_position(self, position:int):
        self.main_window.write_slider.setValue(position)
    
    def save_video_buffer(self):
        self.main_window.save_buffer_button.setEnabled(False)
        #QTimer.singleShot(3000, lambda: self.main_window.save_buffer_button.setEnabled(True))
        self.worker_thread.save_video_buffer()
        

    def update_frame(self, display_frame: np.ndarray):
        ''' The frame emitted by the WorkerThread is shown on the corresponding QLabel as a QImage.

            Arguments:
            -display_frame (np.ndarray): The frame emitted by the thread
        '''
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        q_image = q_image.scaled(self.main_window.video_label_1.width(),self.main_window.video_label_1.height(), 
                                 Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation )

        pixmap = QPixmap.fromImage(q_image)
        self.main_window.video_label_1.setPixmap(pixmap)

