"""
Backup script for CountyDataSync database files.

This script creates backups of database files with timestamps,
useful for scheduled backups in CI/CD pipelines.
"""
import shutil
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_databases():
    """
    Create timestamped backups of database files.
    """
    # Define the backup directory and create it if it doesn't exist
    backup_dir = 'backup'
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Backup directory: {backup_dir}")
    
    # List all database files to backup
    files_to_backup = [
        'output/stats_db.sqlite', 
        'output/working_db.sqlite', 
        'output/geo_db.gpkg'
    ]
    
    # Create timestamp for the backup files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Copy each file to the backup directory with a timestamp
    backup_files = []
    for file in files_to_backup:
        if os.path.exists(file):
            dest = os.path.join(backup_dir, f"{os.path.basename(file)}.{timestamp}.bak")
            shutil.copy(file, dest)
            backup_files.append(dest)
            logger.info(f"Backed up {file} to {dest}")
        else:
            logger.warning(f"Warning: {file} not found, skipping backup")
    
    # Return the list of backup files created
    return backup_files

if __name__ == "__main__":
    try:
        backup_files = backup_databases()
        if backup_files:
            logger.info(f"Backup completed successfully. Created {len(backup_files)} backup files.")
        else:
            logger.warning("No files were backed up.")
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        raise