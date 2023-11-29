from PySide6.QtCore import QThread, QMutex, Signal
import cv2
import numpy as np
from CircularBuffer import CircularBuffer

class WorkerThread(QThread):
    display_frame = Signal(np.ndarray)
    head_position_updated = Signal(int)
    tail_position_updated = Signal(int)

    def __init__(self, buffer: CircularBuffer, capture_index: int = None, parent=None):
        '''QThread that processes frame from a VideoCapture by writing and reading a CircularBuffer and emits them on the GUI.
        
            Arguments:
            buffer (CircularBuffer): The CircularBuffer where frames are saved and retrieved.
            capture_index (int): VideoCapture index to a specific webcam
            parent: Parent QObject.
        '''
        super().__init__(parent)
        if not isinstance(buffer, CircularBuffer) or buffer == None:
            raise TypeError("Argument 'buffer' is None or is not a CircularBuffer object")
        
        # Data containers
        self.video_capture = None
        self.buffer = buffer

        # Flags
        self.is_stopped = False
        self.is_playback = False
        self.is_peeking = False

        # Values
        self.peek_position = 0

        # Mutex for thread safety
        self.mutex = QMutex()

        if not(capture_index, int) or capture_index == None:
            raise TypeError("Argument 'capture_index' is None or is not of int type")
        else:
            try:
                self.video_capture = cv2.VideoCapture(capture_index)
                self.width = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                self.height = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                self.fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                self.fps = 25
            except:
                raise SystemError("Argument 'capture_index' is not a valid index for cv2.VideoCapture object")


    def run(self):
        ''' Overrided method from the QThread class. The VideoCapture frames are processed until an exception or the thread is stopped.'''

        if not self.video_capture.isOpened():
            raise Exception("ERROR: Couldn't open VideoCapture")

        while not self.is_stopped:
            ret, frame = self.video_capture.read()

            if not ret:
                raise Exception("ERROR: Couldn't read from VideoCapture")
            
            self.mutex.lock()
            # Writing the current frame at the head of the buffer
            self.buffer.write_frame(frame)

            # If the user is dragging the timeline cursor the frame shown corresponds to the position on the timeline
            # If the user isn't dragging the timeline cursor the frae shown is the one at the tail of the buffer
            if self.is_peeking:
                display_frame = self.buffer.peek_frame(self.peek_position)
            else:
                display_frame = self.buffer.read_frame()

            # Emitting signals to update the GUI
            self.display_frame.emit(display_frame)
            self.head_position_updated.emit(self.buffer.head_position())
            self.tail_position_updated.emit(self.buffer.tail_position())

            self.mutex.unlock()
      
    def stop(self):
        self.mutex.lock()
        self.is_stopped = True
        self.wait()
        self.mutex.unlock()

    def save_video_buffer(self):
        '''The current CircularBuffer is saved to disk as a video using OpenCV VideoWriter'''
        self.mutex.lock()
        auxiliary_buffer = self.buffer.get_buffer()
        self.mutex.unlock()
        writer = cv2.VideoWriter('output.avi', self.fourcc, self.fps, (int(self.width), int(self.height)))

        for frame in auxiliary_buffer:
            writer.write(frame)

    def set_buffer_peeking(self, is_peeking: bool, new_peek_position: int = None):
        ''' When the thread is peeking playback frames are shown by indexing the CircularBuffer.
        
            Arguments:
            is_peeking (bool): Flag that enables or disables the thread peeking through the buffer.
            new_peek_position (int): Buffer index where the thread will peek at the next frame.
        '''
        self.mutex.lock()
        self.is_peeking = is_peeking
        self.peek_position = new_peek_position
        self.mutex.unlock()
