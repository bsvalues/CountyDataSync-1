"""
Utility functions for the ETL process.
"""
import os
import psutil
from datetime import datetime


def ensure_directory_exists(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory (str): Path to the directory to check/create
    
    Returns:
        str: Path to the directory
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_timestamp():
    """
    Get a formatted timestamp for use in filenames.
    
    Returns:
        str: Formatted timestamp (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def get_memory_usage():
    """
    Get the current memory usage of the process.
    
    Returns:
        float: Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)  # Convert to MB

# Alias for backward compatibility
get_memory_usage_value = get_memory_usage


def get_cpu_usage():
    """
    Get the current CPU usage.
    
    Returns:
        float: CPU usage as a percentage
    """
    return psutil.cpu_percent(interval=0.1)


def format_elapsed_time(seconds):
    """
    Format elapsed time in a human-readable format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"
    else:
        hours = int(seconds / 3600)
        remaining = seconds % 3600
        minutes = int(remaining / 60)
        remaining_seconds = remaining % 60
        return f"{hours}h {minutes}m {remaining_seconds:.2f}s"


def check_file_size(file_path):
    """
    Check the size of a file in KB.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        float: File size in KB
    """
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / 1024  # Convert to KB
    return 0