from PySide6.QtCore import QThread, QMutex, QMutexLocker, Signal, QWaitCondition, QElapsedTimer
import cv2
import numpy as np
import threading
from CircularBuffer import CircularBuffer
import time

class VideoCaptureThread(QThread):
    display_frame = Signal(np.ndarray)
    head_position_updated = Signal(int)
    tail_position_updated = Signal(int)

    def __init__(self, buffer_size: int, capture_index: int = None, parent=None):
        super().__init__()
        '''QThread that processes frame from a VideoCapture by writing and reading a CircularBuffer and emits them on the GUI.
        
            Arguments:
            -buffer_size (int): The CircularBuffer size in frames.
            -capture_index (int): VideoCapture index to a specific webcam
            -parent: Parent QObject.
        ''' 
        # Data containers
        self.video_capture = None
        self.buffer = CircularBuffer(buffer_size)

        # Flags
        self.is_stopped = False
        self.is_playback = False
        self.is_peeking = False

        # Values
        self.peek_position = 0

        # Mutex for thread safety
        self.mutex = QMutex()
        # QWaitCondition for synchronization
        self.sync_condition = QWaitCondition()

        if not(capture_index, int) or capture_index is None:
            raise TypeError("Argument 'capture_index' is None or is not of int type")
        else:
            try:
                self.video_capture = cv2.VideoCapture(capture_index, cv2.CAP_MSMF)                
                self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                self.width = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                self.height = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                #self.video_capture.set(cv2.CAP_PROP_FPS, 25 )
                self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                self.frame_interval = (1 / self.fps) * 1000
                print("\n---------")
                print("Video Capture Thread CREATED")
                print(f"Capture Index: {capture_index} | Buffer Size: {buffer_size} | Width: {self.width} | Height: {self.height} | FPS: {self.fps}")
                print("---------\n")
            except:
                raise SystemError(f"Argument 'capture_index' = {capture_index} is not a valid index for cv2.VideoCapture object")


    def run(self):
        ''' Overrided method from the QThread class. The VideoCapture frames are processed until an exception or the thread is stopped.
            This thread is based on a CircularBuffer object on which it writes and read the video frame in input from an OpenCV VideoCapture
        '''
        if not self.video_capture.isOpened():
            raise Exception("ERROR: Couldn't open VideoCapture")

        while not self.is_stopped:
        
            with QMutexLocker(self.mutex):
                self.sync_condition.wait(self.mutex)

                ret, frame = self.video_capture.read()

                if not ret:
                    raise Exception("ERROR: Couldn't read from VideoCapture")
                
                # Writing the current frame at the head of the buffer
                if not self.is_playback:
                    self.buffer.write_frame(frame)

                # If the user is dragging the timeline cursor the frame shown corresponds to the position on the timeline
                # If the user isn't dragging the timeline cursor the frae shown is the one at the tail of the buffer
                if self.is_peeking:
                    display_frame = self.buffer.peek_frame(self.peek_position)
                else:
                    display_frame = self.buffer.read_frame(playback=self.is_playback)

                # Emitting signals to update the GUI
                self.head_position_updated.emit(self.buffer.head_position())
                self.tail_position_updated.emit(self.buffer.tail_position())
                self.display_frame.emit(display_frame)

    def synchronize_threads(self):
        # Emit signal to synchronize all threads
        with QMutexLocker(self.mutex):
            synch_time = time.time()
            print(f"Thread: {self} synch at time: {synch_time}")
            self.sync_condition.wakeAll() 

    def stop(self):
        with QMutexLocker(self.mutex):
            self.is_stopped = True
        self.wait()
    
    def get_capture_data(self) -> tuple[list, int, int, int]:
        '''Return a tuple containing the buffer and capture data.

            Returns:
            -Content of the circular buffer as a list
            -Frame width and height
            -Video FPS
        '''
        with QMutexLocker(self.mutex):
            buffer = self.buffer.get_buffer()
            capture_parameters = [buffer, self.width, self.height, self.fps]
            
        return capture_parameters

    def set_buffer_peeking(self, is_peeking: bool, new_peek_position: int = None):
        ''' When the thread is peeking playback frames are shown by indexing the CircularBuffer.
        
            Arguments:
            -is_peeking (bool): Flag that enables or disables the thread peeking through the buffer.
            -new_peek_position (int): Buffer index where the thread will peek at the next frame.
        '''
        with QMutexLocker(self.mutex):
            self.is_peeking = is_peeking
            self.peek_position = new_peek_position

            if not is_peeking:
                self.buffer.set_tail_position(new_peek_position)

    def set_buffer_playback(self, is_playback:bool):
        '''When the playback is selected the head pointer in the buffer stops and no new frame are written. The playback is done with the tail
            pointer starting from the beginning.

            Arguments:
            -is_playback(bool): Flag that enables or disables the buffer playback.
        '''
        with QMutexLocker(self.mutex):
            self.is_playback = is_playback
            if is_playback:
                self.buffer.set_tail_position(position=0)
            else:
                self.buffer.set_tail_to_head()