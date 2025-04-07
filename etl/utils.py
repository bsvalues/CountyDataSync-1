"""
Utility functions for the CountyDataSync ETL process.
"""
import os
import logging
import time
import psutil
import datetime

logger = logging.getLogger(__name__)

def get_memory_usage():
    """
    Get the current memory usage of the process.
    
    Returns:
        str: Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    return f"{memory_mb:.2f} MB"

def format_elapsed_time(start_time):
    """
    Format the elapsed time in a human-readable format.
    
    Args:
        start_time (float): Start time in seconds since epoch
        
    Returns:
        str: Formatted elapsed time
    """
    elapsed_seconds = time.time() - start_time
    
    if elapsed_seconds < 60:
        return f"{elapsed_seconds:.2f} seconds"
    elif elapsed_seconds < 3600:
        minutes = int(elapsed_seconds // 60)
        seconds = elapsed_seconds % 60
        return f"{minutes} minutes {seconds:.2f} seconds"
    else:
        hours = int(elapsed_seconds // 3600)
        minutes = int((elapsed_seconds % 3600) // 60)
        seconds = elapsed_seconds % 60
        return f"{hours} hours {minutes} minutes {seconds:.2f} seconds"

def get_timestamp():
    """
    Get the current timestamp in a formatted string.
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def ensure_directory_exists(directory_path):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.debug(f"Created directory: {directory_path}")

def create_output_filename(base_name, extension, timestamp=False):
    """
    Create an output filename with optional timestamp.
    
    Args:
        base_name (str): Base name for the file
        extension (str): File extension
        timestamp (bool): Whether to include a timestamp
        
    Returns:
        str: Output filename
    """
    if timestamp:
        ts = get_timestamp()
        return f"{base_name}_{ts}.{extension}"
    else:
        return f"{base_name}.{extension}"

def check_file_size(file_path):
    """
    Check the size of a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: File size in a human-readable format
    """
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.2f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.2f} GB"
    else:
        return "File not found"
