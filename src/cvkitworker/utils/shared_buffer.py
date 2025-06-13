import numpy as np
from multiprocessing import shared_memory
from typing import List, Optional

class SharedMemoryCircularBuffer:
    """Circular buffer backed by :class:`multiprocessing.shared_memory.SharedMemory`."""

    def __init__(
        self,
        frame_shape: tuple,
        dtype: np.dtype,
        capacity: int,
        name: Optional[str] = None,
        create: bool = True,
    ):
        self.frame_shape = tuple(frame_shape)
        self.dtype = np.dtype(dtype)
        self.capacity = int(capacity)
        self.frame_size = int(np.prod(self.frame_shape)) * self.dtype.itemsize
        self.total_size = self.frame_size * self.capacity

        if create:
            self.shm = shared_memory.SharedMemory(create=True, size=self.total_size, name=name)
            self.owns_shm = True
        else:
            if name is None:
                raise ValueError("Must specify name when create=False")
            self.shm = shared_memory.SharedMemory(name=name)
            self.owns_shm = False

        self.buffer = np.ndarray(
            (self.capacity,) + self.frame_shape,
            dtype=self.dtype,
            buffer=self.shm.buf,
        )

        self.index = 0
        self.length = 0

    @property
    def name(self) -> str:
        """Return the shared memory block name."""
        return self.shm.name

    def append(self, frame: np.ndarray) -> None:
        """Append a frame to the buffer, overwriting the oldest if full."""
        if frame.shape != self.frame_shape or frame.dtype != self.dtype:
            raise ValueError("Frame has incompatible shape or dtype")
        np.copyto(self.buffer[self.index], frame)
        self.index = (self.index + 1) % self.capacity
        if self.length < self.capacity:
            self.length += 1

    def get_last(self) -> np.ndarray:
        """Return a copy of the most recently added frame."""
        if self.length == 0:
            raise IndexError("Buffer is empty")
        idx = (self.index - 1) % self.capacity
        return self.buffer[idx].copy()

    def get_all(self) -> List[np.ndarray]:
        """Return copies of all frames in the buffer in insertion order."""
        if self.length == 0:
            return []
        frames = []
        start = (self.index - self.length) % self.capacity
        for i in range(self.length):
            idx = (start + i) % self.capacity
            frames.append(self.buffer[idx].copy())
        return frames

    def close(self) -> None:
        """Close and unlink shared memory if owned."""
        self.shm.close()
        if self.owns_shm:
            self.shm.unlink()
