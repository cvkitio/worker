import sys
from pathlib import Path
import numpy as np

# Ensure project src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.utils.shared_buffer import SharedMemoryCircularBuffer


class TestSharedMemoryCircularBuffer:
    def test_append_and_get_last(self):
        buf = SharedMemoryCircularBuffer(frame_shape=(2, 2, 3), dtype=np.uint8, capacity=2)
        f1 = np.ones((2, 2, 3), dtype=np.uint8)
        f2 = np.ones((2, 2, 3), dtype=np.uint8) * 2
        buf.append(f1)
        assert np.array_equal(buf.get_last(), f1)
        buf.append(f2)
        assert np.array_equal(buf.get_last(), f2)
        buf.close()

    def test_overwrite_and_get_all(self):
        buf = SharedMemoryCircularBuffer(frame_shape=(1, 1, 1), dtype=np.uint8, capacity=3)
        for i in range(5):
            buf.append(np.full((1, 1, 1), i, dtype=np.uint8))
        frames = buf.get_all()
        expected = [np.array([[[2]]], dtype=np.uint8),
                    np.array([[[3]]], dtype=np.uint8),
                    np.array([[[4]]], dtype=np.uint8)]
        assert len(frames) == 3
        for a, e in zip(frames, expected):
            assert np.array_equal(a, e)
        buf.close()
