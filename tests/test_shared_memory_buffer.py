import sys
from pathlib import Path
import numpy as np

# Ensure project src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.utils.shared_buffer import SharedMemoryCircularBuffer


def _worker(name: str, shape: tuple, dtype: str, capacity: int):
    import numpy as np
    from cvkitworker.utils.shared_buffer import SharedMemoryCircularBuffer

    buf = SharedMemoryCircularBuffer(
        frame_shape=shape, dtype=np.dtype(dtype), capacity=capacity,
        name=name, create=False
    )
    buf.append(np.full(shape, 1, dtype=np.dtype(dtype)))
    buf.append(np.full(shape, 2, dtype=np.dtype(dtype)))
    last = buf.get_last()
    all_frames = buf.get_all()
    buf.close()
    return last, all_frames


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

    def test_process_pool_access(self):
        """Shared memory buffer should be usable from a subprocess."""
        from concurrent.futures import ProcessPoolExecutor

        shape = (1, 1, 1)
        buf = SharedMemoryCircularBuffer(frame_shape=shape, dtype=np.uint8, capacity=2)
        with ProcessPoolExecutor(max_workers=1) as ex:
            result = ex.submit(_worker, buf.name, shape, 'uint8', 2).result()

        last, frames = result
        assert np.array_equal(last, np.full(shape, 2, dtype=np.uint8))
        assert len(frames) == 2
        assert np.array_equal(frames[0], np.full(shape, 1, dtype=np.uint8))
        assert np.array_equal(frames[1], np.full(shape, 2, dtype=np.uint8))
        buf.close()
    
    def test_pythonic_features(self):
        """Test Pythonic interface methods."""
        with SharedMemoryCircularBuffer(frame_shape=(1, 1, 1), dtype=np.uint8, capacity=3) as buf:
            # Test len and is_full
            assert len(buf) == 0
            assert not buf.is_full
            
            # Add frames
            for i in range(3):
                buf.append(np.full((1, 1, 1), i, dtype=np.uint8))
            
            assert len(buf) == 3
            assert buf.is_full
            
            # Test iteration
            frames = list(buf)
            assert len(frames) == 3
            for i, frame in enumerate(frames):
                assert np.array_equal(frame, np.full((1, 1, 1), i, dtype=np.uint8))
            
            # Test indexing
            assert np.array_equal(buf[0], np.full((1, 1, 1), 0, dtype=np.uint8))
            assert np.array_equal(buf[-1], np.full((1, 1, 1), 2, dtype=np.uint8))
            assert np.array_equal(buf[1], np.full((1, 1, 1), 1, dtype=np.uint8))
            
            # Test clear
            buf.clear()
            assert len(buf) == 0
            assert not buf.is_full
