#!/usr/bin/env python
"""
CountyDataSync Backup Script

This script creates backups of all databases used by CountyDataSync:
- GeoPackage spatial database
- SQLite statistics database
- SQLite working database

The backups are timestamped and stored in a configurable backup directory.
Older backups can be automatically pruned based on retention settings.
Optional Azure Blob Storage backup is supported.

Usage:
  python backup_script.py [--config CONFIG_PATH] [--backup-dir DIRECTORY]
                         [--retention DAYS] [--verbose] [--azure]
"""

import os
import sys
import shutil
import sqlite3
import logging
import argparse
import datetime
import zipfile
from pathlib import Path
import configparser
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backup.log')
    ]
)
logger = logging.getLogger('backup')

# Default configurations
DEFAULT_CONFIG = {
    'backup_dir': 'backups',
    'retention_days': 30,
    'databases': {
        'geo_db': 'geo_db.gpkg',
        'stats_db': 'stats_db.sqlite',
        'working_db': 'working_db.sqlite'
    },
    'azure': {
        'enabled': False,
        'connection_string': '',
        'container_name': 'countydata-backups'
    }
}

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='CountyDataSync Backup Tool')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--backup-dir', type=str, help='Directory to store backups')
    parser.add_argument('--retention', type=int, help='Number of days to retain backups')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--azure', action='store_true', help='Enable Azure Blob Storage backup')
    return parser.parse_args()

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults."""
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(config_path)
            
            if 'Backup' in config_parser:
                backup_section = config_parser['Backup']
                if 'backup_dir' in backup_section:
                    config['backup_dir'] = backup_section['backup_dir']
                if 'retention_days' in backup_section:
                    config['retention_days'] = int(backup_section['retention_days'])
            
            if 'Databases' in config_parser:
                db_section = config_parser['Databases']
                for key in config['databases']:
                    if key in db_section:
                        config['databases'][key] = db_section[key]
                        
            if 'Azure' in config_parser:
                azure_section = config_parser['Azure']
                if 'enabled' in azure_section:
                    config['azure']['enabled'] = azure_section.getboolean('enabled')
                if 'connection_string' in azure_section:
                    config['azure']['connection_string'] = azure_section['connection_string']
                if 'container_name' in azure_section:
                    config['azure']['container_name'] = azure_section['container_name']
                        
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    return config

def verify_database_integrity(db_path: str) -> bool:
    """Verify SQLite database integrity before backup."""
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return False
        
    # Skip integrity check for non-SQLite files (like GeoPackage)
    if not db_path.endswith('.sqlite'):
        return True
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 'ok':
            logger.info(f"Database integrity check passed: {db_path}")
            return True
        else:
            logger.error(f"Database integrity check failed: {db_path}, Result: {result[0]}")
            return False
    except Exception as e:
        logger.error(f"Error checking database integrity: {db_path}, Error: {e}")
        return False

def create_backup_directory(backup_dir: str) -> str:
    """Create timestamped backup directory."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_backup_dir = os.path.join(backup_dir, f"backup_{timestamp}")
    
    try:
        os.makedirs(full_backup_dir, exist_ok=True)
        logger.info(f"Created backup directory: {full_backup_dir}")
        return full_backup_dir
    except Exception as e:
        logger.error(f"Error creating backup directory: {e}")
        raise

def backup_database(db_path: str, backup_dir: str) -> Optional[str]:
    """Copy database file to backup directory."""
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found: {db_path}")
        return None
        
    try:
        db_name = os.path.basename(db_path)
        backup_path = os.path.join(backup_dir, db_name)
        shutil.copy2(db_path, backup_path)
        logger.info(f"Successfully backed up {db_path} to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up database {db_path}: {e}")
        return None

def create_archive(backup_dir: str) -> Optional[str]:
    """Create a ZIP archive of the backup directory."""
    try:
        archive_path = f"{backup_dir}.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(backup_dir))
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created backup archive: {archive_path}")
        return archive_path
    except Exception as e:
        logger.error(f"Error creating backup archive: {e}")
        return None

def upload_to_azure(archive_path: str, azure_config: Dict[str, Any]) -> bool:
    """Upload backup archive to Azure Blob Storage."""
    if not azure_config.get('enabled', False):
        logger.info("Azure Blob Storage backup is disabled")
        return False
    
    if not azure_config.get('connection_string'):
        logger.error("Azure connection string is missing")
        return False
    
    try:
        # Import Azure libraries only when needed
        from azure.storage.blob import BlobServiceClient
        
        # Get blob service client
        blob_service_client = BlobServiceClient.from_connection_string(
            azure_config['connection_string']
        )
        
        # Get container client
        container_name = azure_config['container_name']
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
            logger.info(f"Created Azure container: {container_name}")
        
        # Upload backup archive
        blob_name = os.path.basename(archive_path)
        with open(archive_path, "rb") as data:
            blob_client = container_client.upload_blob(name=blob_name, data=data, overwrite=True)
            logger.info(f"Uploaded backup to Azure: {blob_name}")
        return True
    except ImportError:
        logger.error("Azure Storage SDK not installed. Run: pip install azure-storage-blob")
        return False
    except Exception as e:
        logger.error(f"Error uploading to Azure: {str(e)}")
        return False

def cleanup_old_backups(backup_dir: str, retention_days: int) -> None:
    """Remove backup directories and archives older than retention_days."""
    if retention_days <= 0:
        logger.info("Retention policy disabled, skipping cleanup")
        return
        
    try:
        current_time = datetime.datetime.now()
        retention_delta = datetime.timedelta(days=retention_days)
        
        # Clean up backup directories
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            
            # Skip non-backup items
            if not (item.startswith("backup_") or item.startswith("backup_") and item.endswith(".zip")):
                continue
                
            # Get creation time and calculate age
            created_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            age = current_time - created_time
            
            if age > retention_delta:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                logger.info(f"Removed old backup: {item_path} (age: {age.days} days)")
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

def generate_backup_report(success: bool, backup_results: Dict[str, Tuple[bool, str]]) -> str:
    """Generate a backup health report."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = [
        f"CountyDataSync Backup Report - {timestamp}",
        f"Overall Status: {'SUCCESS' if success else 'FAILURE'}",
        "\nDatabase Backup Results:",
    ]
    
    for db_name, (db_success, message) in backup_results.items():
        status = "✓" if db_success else "✗"
        report.append(f"  {status} {db_name}: {message}")
    
    return "\n".join(report)

def main() -> int:
    """Main backup function."""
    args = parse_arguments()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.backup_dir:
        config['backup_dir'] = args.backup_dir
    if args.retention:
        config['retention_days'] = args.retention
    if args.azure:
        config['azure']['enabled'] = True
        
    # Create main backup directory if it doesn't exist
    try:
        os.makedirs(config['backup_dir'], exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create main backup directory: {e}")
        return 1
        
    # Create timestamped backup directory
    try:
        backup_timestamp_dir = create_backup_directory(config['backup_dir'])
    except Exception:
        return 1
        
    # Backup each database
    backup_success = True
    backup_results = {}
    
    for db_name, db_path in config['databases'].items():
        logger.info(f"Processing backup for {db_name}: {db_path}")
        
        # Verify database integrity
        if verify_database_integrity(db_path):
            # Backup the database
            backup_result = backup_database(db_path, backup_timestamp_dir)
            if backup_result:
                backup_results[db_name] = (True, "Successfully backed up")
            else:
                backup_results[db_name] = (False, "Backup failed")
                backup_success = False
        else:
            backup_results[db_name] = (False, "Integrity check failed")
            logger.error(f"Skipping backup of {db_name} due to integrity check failure")
            backup_success = False
    
    # Create a zip archive of the backup
    archive_path = None
    if backup_success:
        archive_path = create_archive(backup_timestamp_dir)
        if not archive_path:
            backup_success = False
    
    # Upload to Azure if enabled
    azure_success = False
    if backup_success and archive_path and config['azure']['enabled']:
        azure_success = upload_to_azure(archive_path, config['azure'])
        if azure_success:
            logger.info("Successfully uploaded backup to Azure Blob Storage")
        else:
            logger.warning("Failed to upload backup to Azure Blob Storage")
    
    # Clean up old backups
    cleanup_old_backups(config['backup_dir'], config['retention_days'])
    
    # Generate backup report
    report = generate_backup_report(backup_success, backup_results)
    logger.info("\n" + report)
    
    # Save report to file
    report_path = os.path.join(config['backup_dir'], "last_backup_report.txt")
    try:
        with open(report_path, 'w') as f:
            f.write(report)
    except Exception as e:
        logger.error(f"Failed to save backup report: {e}")
    
    if backup_success:
        logger.info("Backup process completed successfully")
        return 0
    else:
        logger.error("Backup process completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
