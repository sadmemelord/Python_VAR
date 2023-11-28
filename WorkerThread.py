from PySide6.QtCore import QThread, Signal
import cv2
import numpy as np
from CircularBuffer import CircularBuffer

class WorkerThread(QThread):
    frame_processed = Signal(np.ndarray)
    head_position_updated = Signal(int)
    tail_position_updated = Signal(int)

    def __init__(self, buffer: CircularBuffer, parent=None):
        super().__init__(parent)
        if not isinstance(buffer, CircularBuffer) or buffer == None:
            raise Exception("ERROR: Argument 'buffer' is None or is not a CircularBuffer object")
        
        # Data containers
        self.video_capture = None
        self.buffer = buffer

        # Flags
        self.is_stopped = False
        self.is_peeking = False

        # Values
        self.peek_position = 0

    def run(self):
        self.video_capture = cv2.VideoCapture(0)
        
        if not self.video_capture.isOpened():
            raise Exception("ERROR: Couldn't open VideoCapture")

        while not self.is_stopped:
            ret, frame = self.video_capture.read()

            if not ret:
                raise Exception("ERROR: Couldn't read from VideoCapture")
            
            # Writing the current frame at the head of the buffer
            self.buffer.write_frame(frame)

            # If the user is dragging the timeline cursor the frame shown corresponds to the position on the timeline
            # If the user isn't dragging the timeline cursor the frae shown is the one at the tail of the buffer
            if self.is_peeking:
                display_frame = self.buffer.peek_frame(self.peek_position)
            else:
                display_frame = self.buffer.read_frame()

            # Emitting the signal to update the displayed frame ad the timeline cursors
            self.frame_processed.emit(display_frame)
            self.head_position_updated.emit(self.buffer.get_head_position())
            self.tail_position_updated.emit(self.buffer.get_tail_position())

            
    def stop(self):
        self.is_stopped = True
        self.wait()
    
    def set_buffer_peeking(self, is_peeking: bool, new_peek_position: int = None):
        
        self.is_peeking = is_peeking
        self.peek_position = new_peek_position
