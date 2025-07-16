"""
Timing measurement utilities for computer vision operations.
Provides decorators and storage interfaces for performance monitoring.
"""

import time
import functools
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
from pathlib import Path
from loguru import logger


class TimingStorage(ABC):
    """Abstract interface for storing timing measurements."""
    
    @abstractmethod
    def store_timing(self, measurement: Dict[str, Any]) -> None:
        """Store a timing measurement."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any pending measurements."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close storage and clean up resources."""
        pass


class FileTimingStorage(TimingStorage):
    """File-based timing storage implementation."""
    
    def __init__(self, file_path: str = "timing_measurements.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
    def store_timing(self, measurement: Dict[str, Any]) -> None:
        """Store timing measurement as JSON line in file."""
        try:
            with open(self.file_path, 'a') as f:
                f.write(json.dumps(measurement) + '\n')
        except Exception as e:
            logger.error(f"Failed to store timing measurement: {e}")
    
    def flush(self) -> None:
        """File storage auto-flushes, no action needed."""
        pass
    
    def close(self) -> None:
        """File storage auto-closes, no action needed."""
        pass


class DatabaseTimingStorage(TimingStorage):
    """Database timing storage implementation (placeholder for future)."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # TODO: Implement database connection
        logger.info("Database timing storage not yet implemented")
    
    def store_timing(self, measurement: Dict[str, Any]) -> None:
        # TODO: Implement database storage
        logger.debug(f"Would store to DB: {measurement}")
    
    def flush(self) -> None:
        # TODO: Implement database flush
        pass
    
    def close(self) -> None:
        # TODO: Implement database close
        pass


class TelemetryTimingStorage(TimingStorage):
    """Telemetry system timing storage implementation (placeholder for future)."""
    
    def __init__(self, endpoint: str, api_key: str = None):
        self.endpoint = endpoint
        self.api_key = api_key
        # TODO: Implement telemetry connection
        logger.info("Telemetry timing storage not yet implemented")
    
    def store_timing(self, measurement: Dict[str, Any]) -> None:
        # TODO: Implement telemetry storage
        logger.debug(f"Would send to telemetry: {measurement}")
    
    def flush(self) -> None:
        # TODO: Implement telemetry flush
        pass
    
    def close(self) -> None:
        # TODO: Implement telemetry close
        pass


class TimingManager:
    """Manages timing measurement configuration and storage."""
    
    def __init__(self):
        self.enabled = self._get_timing_enabled()
        self.storage = self._create_storage() if self.enabled else None
        
    def _get_timing_enabled(self) -> bool:
        """Check if timing measurement is enabled via environment or config."""
        # Check environment variable first
        env_enabled = os.getenv('CVKIT_TIMING_ENABLED', '').lower()
        if env_enabled in ('true', '1', 'yes', 'on'):
            return True
        elif env_enabled in ('false', '0', 'no', 'off'):
            return False
        
        # Check global config if available
        try:
            from ..config.parse_config import ConfigParser
            # Try to load from default config files
            config_files = ['config.json', 'config.sample.json']
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        parser = ConfigParser(config_file)
                        timing_config = parser.get('timing', {})
                        if isinstance(timing_config, dict):
                            return timing_config.get('enabled', False)
                        elif isinstance(timing_config, bool):
                            return timing_config
                    except Exception:
                        continue
        except ImportError:
            pass
        
        # Default to disabled
        return False
    
    def _create_storage(self) -> TimingStorage:
        """Create appropriate storage backend based on configuration."""
        storage_type = os.getenv('CVKIT_TIMING_STORAGE', 'file').lower()
        
        if storage_type == 'file':
            output_path = os.getenv('CVKIT_TIMING_FILE', 'logs/timing_measurements.jsonl')
            return FileTimingStorage(output_path)
        elif storage_type == 'database':
            connection_string = os.getenv('CVKIT_TIMING_DB_CONNECTION', '')
            return DatabaseTimingStorage(connection_string)
        elif storage_type == 'telemetry':
            endpoint = os.getenv('CVKIT_TIMING_TELEMETRY_ENDPOINT', '')
            api_key = os.getenv('CVKIT_TIMING_TELEMETRY_API_KEY', '')
            return TelemetryTimingStorage(endpoint, api_key)
        else:
            logger.warning(f"Unknown timing storage type: {storage_type}, defaulting to file")
            return FileTimingStorage()
    
    def record_timing(self, function_name: str, duration_ms: float, 
                     context: Dict[str, Any] = None) -> None:
        """Record a timing measurement."""
        if not self.enabled or not self.storage:
            return
        
        measurement = {
            'timestamp': datetime.utcnow().isoformat(),
            'function': function_name,
            'duration_ms': duration_ms,
            'process_id': os.getpid(),
            'context': context or {}
        }
        
        self.storage.store_timing(measurement)
    
    def flush(self) -> None:
        """Flush any pending measurements."""
        if self.storage:
            self.storage.flush()
    
    def close(self) -> None:
        """Close timing manager and clean up resources."""
        if self.storage:
            self.storage.close()


# Global timing manager instance
_timing_manager = None


def get_timing_manager() -> TimingManager:
    """Get global timing manager instance."""
    global _timing_manager
    if _timing_manager is None:
        _timing_manager = TimingManager()
    return _timing_manager


def measure_timing(function_name: Optional[str] = None, 
                  include_args: bool = False,
                  include_result: bool = False):
    """
    Decorator to measure execution time of functions.
    
    Args:
        function_name: Override function name in measurements
        include_args: Include function arguments in context
        include_result: Include function result info in context
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timing_manager = get_timing_manager()
            
            if not timing_manager.enabled:
                # If timing is disabled, just call the function
                return func(*args, **kwargs)
            
            # Prepare context information
            # Check if this is a method call (first arg is 'self' - has methods from the function's class)
            is_method = False
            if args:
                try:
                    # Check if first arg has attributes/methods that suggest it's a class instance
                    # and the function is likely a method of that class
                    first_arg = args[0]
                    if (hasattr(first_arg, '__class__') and 
                        hasattr(first_arg, func.__name__) and
                        callable(getattr(first_arg, func.__name__, None))):
                        is_method = True
                except:
                    pass
            
            context = {
                'module': func.__module__,
                'class': getattr(args[0].__class__, '__name__', None) if args and is_method else None,
            }
            
            if include_args:
                try:
                    # Safely include args, avoiding large objects
                    safe_args = []
                    # Skip 'self' if this is a method call
                    start_idx = 1 if is_method else 0
                    
                    for arg in args[start_idx:]:
                        if hasattr(arg, 'shape'):  # NumPy array or similar
                            safe_args.append(f"array{arg.shape}")
                        elif isinstance(arg, (str, int, float, bool)):
                            safe_args.append(arg)
                        else:
                            safe_args.append(str(type(arg).__name__))
                    
                    safe_kwargs = {k: v for k, v in kwargs.items() 
                                 if isinstance(v, (str, int, float, bool))}
                    
                    context['args'] = safe_args
                    context['kwargs'] = safe_kwargs
                except Exception as e:
                    logger.debug(f"Failed to include args in timing context: {e}")
            
            # Measure execution time
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                
                if include_result:
                    try:
                        if hasattr(result, '__len__'):
                            context['result_length'] = len(result)
                        elif hasattr(result, 'shape'):
                            context['result_shape'] = result.shape
                        else:
                            context['result_type'] = type(result).__name__
                    except Exception as e:
                        logger.debug(f"Failed to include result in timing context: {e}")
                
                return result
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                # Record the timing
                measured_function_name = function_name or f"{func.__module__}.{func.__name__}"
                timing_manager.record_timing(measured_function_name, duration_ms, context)
        
        return wrapper
    return decorator


# Convenience decorators for common CV operations
def measure_face_detection(func: Callable) -> Callable:
    """Decorator specifically for face detection functions."""
    return measure_timing("face_detection", include_args=True, include_result=True)(func)


def measure_image_processing(func: Callable) -> Callable:
    """Decorator specifically for image processing functions."""
    return measure_timing("image_processing", include_args=True)(func)


def measure_frame_processing(func: Callable) -> Callable:
    """Decorator specifically for frame processing functions."""
    return measure_timing("frame_processing", include_args=True)(func)


def measure_color_conversion(func: Callable) -> Callable:
    """Decorator specifically for color space conversion functions."""
    return measure_timing("color_conversion", include_args=True)(func)


def measure_scaling(func: Callable) -> Callable:
    """Decorator specifically for scaling/resizing functions."""
    return measure_timing("scaling", include_args=True)(func)