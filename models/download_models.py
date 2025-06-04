import kagglehub
from loguru import logger
import os

# Download latest version
path = kagglehub.dataset_download("leeast/mmod-human-face-detector-dat")

logger.info(f"Path to dataset files: {path} (PID: {os.getpid()})")