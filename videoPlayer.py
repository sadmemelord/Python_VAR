from PySide6.QtCore import Qt, Slot, QMutex, QMutexLocker, QFile, QCoreApplication, QThreadPool, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QMainWindow, QLabel
import numpy as np
import cv2

from VideoCaptureThread import VideoCaptureThread
from VideoWriterThread import VideoWriterThread
from VideoRendererThread import VideoRendererThread

from DialogSettings import DialogSettings

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
        self.buffer_size = 250
        self.encoding = "DIVX"
        self.camera_index = 1
        self.clip_index = 0
        self.number_of_threads = 2
        self.capture_threads = []
        self.renderer_threads = []
        self.writer_threads = []
        self.dialog_settings = None
        
        # Timer used to sync capture threads
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_threads)

        # Function used to connect signals and start threads
        self.prepare_application()


    def prepare_application(self):
        '''Setting UI parameters. Connecting signals and slots. Showing the MainWindow.
        '''

        self.main_window.start_button.clicked.connect(self.start)
        self.main_window.realtime_button.clicked.connect(self.resume_realtime)
        self.main_window.playback_button.clicked.connect(self.restart_playback)
        self.main_window.save_buffer_button.clicked.connect(self.save_video_buffer)
        self.main_window.playback_slider.sliderPressed.connect(self.playback_cursor_pressed)
        self.main_window.playback_slider.sliderMoved.connect(self.playback_cursor_dragged)
        self.main_window.playback_slider.sliderReleased.connect(self.playback_cursor_released)
        self.main_window.actionSettings.triggered.connect(self.open_dialog_settings)

        for thread_index in range(self.number_of_threads):
            # Capture Thread
            c_thread = VideoCaptureThread(buffer_size=self.buffer_size, 
                                                           capture_index=thread_index,
                                                           parent=self)
            
            # Renderer thread
            label_string = "video_label_" + str(thread_index + 1)
            video_label = self.main_window.findChild(QLabel, label_string)
            r_thread = VideoRendererThread(video_label)

            # Connecting signals
            c_thread.tail_position_updated.connect(self.update_playback_cursor_position)
            c_thread.head_position_updated.connect(self.update_write_cursor_position, Qt.DirectConnection)
            c_thread.display_frame.connect(r_thread.video_label_update)

            # Adding threads to their respective list
            self.capture_threads.append(c_thread)
            self.renderer_threads.append(r_thread)
        
        self.setWindowTitle("VAR System Test")
        self.setCentralWidget(self.main_window)
        self.show()
    
    @Slot()
    def restart_playback(self):
        '''Set the tail position to the beginning of the buffer'''
        for thread in self.capture_threads:
            thread.set_buffer_playback(True)

    @Slot()
    def start(self):
    
        self.main_window.playback_slider.setRange(0, self.buffer_size)
        self.main_window.write_slider.setRange(0, self.buffer_size)
        self.main_window.realtime_button.setEnabled(True)
        self.main_window.playback_button.setEnabled(True)
        self.main_window.save_buffer_button.setEnabled(True)
        self.main_window.start_button.setEnabled(False)
        self.main_window.playback_slider.setEnabled(True)
        self.main_window.write_slider.setEnabled(True)

        self.timer.start(self.capture_threads[0].frame_interval)

        for c_thread, r_thread in zip(self.capture_threads, self.renderer_threads):
            c_thread.start()
            r_thread.start()
    @Slot()
    def update_threads(self):
        for thread in self.capture_threads:
            thread.synchronize_threads()

    @Slot(int)
    def update_playback_cursor_position(self, position:int):
        '''The playback cursor is connected to the tail pointer of the buffer. Its position is updated
            through a signal emitted by the WorkerThread.'''
        #print(f"Buffer TAIL position {position}")
        self.main_window.playback_slider.setValue(position)

    @Slot(int)
    def update_write_cursor_position(self, position:int):
        
        #print(f"Buffer HEAD position {position}")
        self.main_window.write_slider.setValue(position)


    @Slot(bool)
    def playback_cursor_pressed(self):
        '''When the playback cursor is pressed the thread stops updating the cursor position'''
        for thread in self.capture_threads:
            thread.tail_position_updated.disconnect(self.update_playback_cursor_position)

    @Slot(int)
    def playback_cursor_dragged(self, slider_value: int):
        '''When the playback cursor is dragged the thread starts peeking at the buffer in the selected position

            Arguments:
            -slider_value (int): The slider value is passed through a signal and determines the index to peek at
        '''
        for thread in self.capture_threads:
            thread.set_buffer_peeking(is_peeking=True, new_peek_position=slider_value)

    @Slot(int)
    def playback_cursor_released(self):
        '''When the playback cursor is released the thread stops peeking at the buffer and resumes playback from the selected position'''
        new_peek_position = self.main_window.playback_slider.value()
        for thread in self.capture_threads:
            thread.set_buffer_peeking(is_peeking=False, new_peek_position=new_peek_position)
            thread.tail_position_updated.connect(self.update_playback_cursor_position)

    @Slot()
    def resume_realtime(self):
        '''Set the tail position to the head position to resume the real-time playback'''
        for thread in self.capture_threads:
            thread.set_buffer_playback(False)

    @Slot()
    def open_dialog_settings(self):
        if not self.dialog_settings:
            self.dialog_settings = DialogSettings()
            self.dialog_settings.updateSettings.connect(self.update_settings)
            self.dialog_settings.show()
        else:
            self.dialog_settings.show()

    @Slot()
    def save_video_buffer(self):
        self.main_window.save_buffer_button.setEnabled(False)

        for index, thread in enumerate(self.capture_threads):
            capture_data = thread.get_capture_data()
            filename = "capture_" + str(index) + "_clip_" + str(self.clip_index) + ".avi"
            self.clip_index += 1

            w_thread = VideoWriterThread(buffer = capture_data[0],
                                        width = int(capture_data[1]),
                                        height = int(capture_data[2]),
                                        fps = capture_data[3],
                                        filename = filename,
                                        fourcc = cv2.VideoWriter_fourcc(*self.encoding),
                                        parent = self)
            
            self.writer_threads.append(w_thread)

        for thread in self.writer_threads:
            thread.start()
        
        #self.video_writer_thread.finished.connect(lambda: self.main_window.save_buffer_button.setEnabled(True))
        self.main_window.save_buffer_button.setEnabled(True)
        
    @Slot(int, int, str)
    def update_settings(self, number_of_cameras, buffer_size, encoding):
        self.buffer_size = buffer_size
        self.number_of_threads = number_of_cameras
        self.encoding = encoding