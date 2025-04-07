#!/usr/bin/env python3
"""
Backup script for CountyDataSync database files.

This script creates backups of database files with timestamps,
useful for scheduled backups in CI/CD pipelines.
"""
import os
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('BackupScript')

def backup_databases():
    """
    Create timestamped backups of database files.
    """
    # Source directories and file patterns
    source_dirs = {
        'output': ['*.gpkg', '*.db', '*.sqlite'],
        'instance': ['*.db', '*.sqlite'],
        '.': ['*.db', '*.sqlite']
    }
    
    # Ensure backup directory exists
    backup_dir = Path('backup')
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_subdir = backup_dir / timestamp
    backup_subdir.mkdir(exist_ok=True)
    
    logger.info(f"Creating backup in {backup_subdir}")
    
    # Track files backed up
    backed_up_files = []
    
    # Copy files to backup directory
    for source_path, patterns in source_dirs.items():
        source_dir = Path(source_path)
        if not source_dir.exists():
            logger.warning(f"Source directory not found: {source_dir}")
            continue
        
        for pattern in patterns:
            for file_path in source_dir.glob(pattern):
                if file_path.is_file():
                    # Create relative subdirectory structure in backup
                    rel_path = file_path.relative_to(Path('.'))
                    target_dir = backup_subdir / rel_path.parent
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    target_path = target_dir / file_path.name
                    try:
                        shutil.copy2(file_path, target_path)
                        logger.info(f"Backed up {file_path} -> {target_path}")
                        backed_up_files.append(str(rel_path))
                    except Exception as e:
                        logger.error(f"Failed to backup {file_path}: {e}")
    
    # Create backup manifest
    manifest_path = backup_subdir / 'manifest.txt'
    try:
        with open(manifest_path, 'w') as f:
            f.write(f"Backup created: {datetime.now().isoformat()}\n")
            f.write(f"Files backed up: {len(backed_up_files)}\n\n")
            for file_path in sorted(backed_up_files):
                f.write(f"{file_path}\n")
        logger.info(f"Backup manifest created: {manifest_path}")
    except Exception as e:
        logger.error(f"Failed to create backup manifest: {e}")
    
    # Clean up old backups (keep the 10 most recent)
    try:
        all_backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], 
                            key=lambda x: x.name, reverse=True)
        
        if len(all_backups) > 10:
            for old_backup in all_backups[10:]:
                logger.info(f"Removing old backup: {old_backup}")
                shutil.rmtree(old_backup)
    except Exception as e:
        logger.error(f"Failed to clean up old backups: {e}")
    
    return len(backed_up_files)

if __name__ == "__main__":
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("Starting database backup...")
    file_count = backup_databases()
    
    if file_count > 0:
        logger.info(f"Backup completed successfully. {file_count} files backed up.")
        sys.exit(0)
    else:
        logger.warning("No files were backed up.")
        sys.exit(1)