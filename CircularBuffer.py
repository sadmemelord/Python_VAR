from collections import deque
from typing import Optional, Any
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.WARNING)

class CircularBuffer:
    """ Basic circular buffer implementation in Python. The following code is used to store and retrieve video frames as numpy arrays
        Attributes:
            capacity (int): The maximum capacity of the buffer.
            buffer (deque): The deque data structure used for storing frames.
            head (int): The index representing the current write position.
            tail (int): The index representing the current read position.
    """
    def __init__(self, capacity: int):
        """Initialize the circular buffer with the given capacity."""

        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
        
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.head = 0
        self.tail = 0

    def write_frame(self, frame: np.ndarray):
        """Write a frame to the buffer at head position. If the buffer is full the oldest frame is replaced"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(frame)
        else:
            self.buffer[self.head] = frame
        self.head = (self.head + 1) % self.capacity

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the buffer at tail position without removing it. Returns None if the buffer is empty."""
        if not self.is_empty():
            frame = self.buffer[self.tail]
            self.tail = (self.tail + 1) % self.capacity
            return frame
        else:
            return None
        
    def peek_frame(self, position: int) -> Optional[np.ndarray]:
        """Read a frame from the buffer in a given position without removing it. Returns None if the buffer is empty"""
        upper_position = self.capacity if self.is_full() else  self.head
        if not self.is_empty():
        
            if 0 <= position <= upper_position:
                return self.buffer[position]
            else:
                logging.warning("Invalid peek position. Frame at head position is returned instead")        
                return self.buffer[-1]
        else:
            return None

    def set_tail_position(self, position: int):
        """Set the tail position."""
        upper_position = self.capacity if self.is_full() else  self.head

        if 0 <= position <= upper_position:
            self.tail = position
        else:
            logging.warning("Invalid tail position. Tail position is now set to head position")
            self.tail = self.head
            
    
    def clear(self):
        """Clear the buffer, removing all elements."""
        self.buffer.clear()
        self.head = 0
        self.tail = 0
    
    def resize(self, new_capacity: int):
        """Resize the buffer to a new capacity."""

        if not isinstance(new_capacity, int) or new_capacity <= 0:
            raise ValueError("New capacity must be a positive integer.")
        
        self.buffer = deque(self.buffer, maxlen=new_capacity)
        self.capacity = new_capacity

    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return not self.buffer

    def is_full(self) -> bool:
        """Check if the buffer is full."""
        return len(self.buffer) == self.capacity

    def get_tail_position(self) -> int:
        """Get the current read position within the buffer."""
        return self.tail

    def get_head_position(self) -> int:
        """Get the current write position within the buffer."""
        return self.head

    def __len__(self) -> int:
        """Return the current size of the buffer."""
        return len(self.buffer)
