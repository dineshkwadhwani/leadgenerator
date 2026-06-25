"""Utility functions and logging setup"""

import logging
import os
from datetime import datetime

# Logger instance
logger = None

def setup_logging():
    """Setup logging configuration"""
    global logger
    
    logger = logging.getLogger('MahaExam')
    logger.setLevel(logging.INFO)
    
    # File handler
    log_file = f"lead_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger():
    """Get logger instance"""
    global logger
    if logger is None:
        setup_logging()
    return logger
