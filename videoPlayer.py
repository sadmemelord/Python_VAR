from PySide6.QtCore import Qt, Slot, QMutex, QFile, QCoreApplication, QThreadPool, QRunnable
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QMainWindow
import numpy as np
import cv2

from VideoCaptureThread import VideoCaptureThread
from VideoWriterThread import VideoWriterThread
from VideoRendererThread import VideoRendererThread

from DialogSettings import DialogSettings

# Set required attributes before creating QGuiApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)


class ThreadRunnable(QRunnable):
    def __init__(self, thread):
        super().__init__()
        self.thread = thread

    def run(self):
        self.thread.start()
        self.thread.wait()

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
        self.dialog_settings = None


        # Mutex for thread sync
        self.mutex = QMutex()

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
                
        self.setWindowTitle("VAR System Test")
        self.setCentralWidget(self.main_window)
        self.show()
    
    def restart_playback(self):
        '''Set the tail position to the beginning of the buffer'''
        for thread in self.capture_threads:
            thread.set_buffer_playback(True)

    def start(self):
        
        thread_pool = QThreadPool.globalInstance()
        thread_pool.setMaxThreadCount(self.number_of_threads)

        for thread_index in range(self.number_of_threads):
            self.capture_threads.append(VideoCaptureThread(buffer_size=self.buffer_size, 
                                                           capture_index=thread_index,
                                                           parent=self))


        self.renderer_threads.append(VideoRendererThread(self.main_window.video_label_1))
        self.renderer_threads.append(VideoRendererThread(self.main_window.video_label_2))
        

        self.main_window.playback_slider.setRange(0, self.buffer_size)
        self.main_window.write_slider.setRange(0, self.buffer_size)

        
        self.main_window.realtime_button.setEnabled(True)
        self.main_window.playback_button.setEnabled(True)
        self.main_window.save_buffer_button.setEnabled(True)
        self.main_window.start_button.setEnabled(False)
        self.main_window.playback_slider.setEnabled(True)
        self.main_window.write_slider.setEnabled(True)

        self.capture_threads[0].tail_position_updated.connect(self.update_playback_cursor_position)
        self.capture_threads[0].head_position_updated.connect(self.update_write_cursor_position)

        self.capture_threads[0].display_frame.connect(self.renderer_threads[0].video_label_update)
        self.capture_threads[1].display_frame.connect(self.renderer_threads[1].video_label_update)

        self.renderer_threads[0].start()
        self.renderer_threads[1].start()
        for thread in self.capture_threads:
            thread.start()
            print(f"Thread: {thread} STARTED")



    @Slot(bool)
    def playback_cursor_pressed(self):
        '''When the playback cursor is pressed the thread stops updating the cursor position'''
        self.mutex.lock()
        #for thread in self.capture_threads:
        self.capture_threads[0].tail_position_updated.disconnect(self.update_playback_cursor_position)
        self.mutex.unlock()

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
        self.capture_threads[0].tail_position_updated.connect(self.update_playback_cursor_position)


    def resume_realtime(self):
        '''Set the tail position to the head position to resume the real-time playback'''
        for thread in self.capture_threads:
            thread.set_buffer_playback(False)
    
    def open_dialog_settings(self):
        if not self.dialog_settings:
            self.dialog_settings = DialogSettings()
            self.dialog_settings.updateSettings.connect(self.update_settings)
            self.dialog_settings.show()
        else:
            self.dialog_settings.show()

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
    
        capture_data = self.capture_threads[0].get_capture_data()
        filename = "clip_" + str(self.clip_index) + ".avi"
        self.clip_index += 1

        self.video_writer_thread = VideoWriterThread(
            buffer = capture_data[0],
            width = int(capture_data[1]),
            height = int(capture_data[2]),
            fps = capture_data[3],
            filename = filename,
            fourcc = cv2.VideoWriter_fourcc(*self.encoding),
            parent = self
        )

        self.video_writer_thread.finished.connect(lambda: self.main_window.save_buffer_button.setEnabled(True))
        self.video_writer_thread.start()
        
    @Slot(int, int, str)
    def update_settings(self, number_of_cameras, buffer_size, encoding):
        self.buffer_size = buffer_size
        self.number_of_threads = number_of_cameras
        self.encoding = encoding

    def update_frame(self, display_frame: np.ndarray):
        ''' The frame emitted by the WorkerThread is shown on the corresponding QLabel as a QImage.

            Arguments:
            -display_frame (np.ndarray): The frame emitted by the thread
        '''
        thread = self.sender()
        thread_index = self.capture_threads.index(thread)

        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        q_image = q_image.scaled(self.main_window.video_label_1.width(),self.main_window.video_label_1.height(), 
                                 Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation )

        pixmap = QPixmap.fromImage(q_image)
        self.main_window.video_label_1.setPixmap(pixmap)
