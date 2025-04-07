#!/usr/bin/env python3
"""
CountyDataSync Standalone ETL Service
-------------------------------------

This script runs the ETL process to synchronize county parcel data.
It can be packaged as a standalone executable using PyInstaller.

Example usage:
    python sync.py
    
Environment variables:
    DATABASE_URL: URL for the PostgreSQL database connection
    USE_TEST_DATA: Set to 'true' to use test data instead of SQL Server
    MSSQL_SERVER: SQL Server hostname/address
    MSSQL_DATABASE: SQL Server database name
    MSSQL_USERNAME: SQL Server username
    MSSQL_PASSWORD: SQL Server password
"""
import os
import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_process.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CountyDataSync')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='CountyDataSync ETL Process')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for data extraction (default: 1000)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory for output files (default: output)')
    parser.add_argument('--test-data', action='store_true',
                        help='Use test data instead of connecting to SQL Server')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    return parser.parse_args()

def configure_environment(args):
    """Configure environment variables based on command line arguments."""
    if args.test_data:
        os.environ['USE_TEST_DATA'] = 'true'
        logger.info("Using test data instead of SQL Server")
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {output_dir.absolute()}")

def run_standalone_etl(batch_size=1000, output_dir='output'):
    """
    Run the ETL process in standalone mode.
    
    Args:
        batch_size (int): Size of batches for data extraction
        output_dir (str): Directory for output files
        
    Returns:
        dict: Dictionary with paths to the created output files and performance metrics
    """
    try:
        # Import here to avoid circular imports
        from etl.sync import run_etl
        
        start_time = time.time()
        logger.info(f"Starting ETL process with batch size {batch_size}")
        
        result = run_etl(batch_size=batch_size)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"ETL process completed in {elapsed_time:.2f} seconds")
        logger.info(f"Output files:")
        for key, path in result.items():
            if isinstance(path, str) and os.path.exists(path):
                logger.info(f"  - {key}: {path} ({os.path.getsize(path) / 1024:.2f} KB)")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in ETL process: {e}", exc_info=True)
        raise

def main():
    """Main entry point."""
    # Process command line arguments
    args = parse_arguments()
    
    # Configure environment
    configure_environment(args)
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    try:
        # Run the ETL process
        result = run_standalone_etl(
            batch_size=args.batch_size,
            output_dir=args.output_dir
        )
        
        # Log success
        logger.info("ETL process completed successfully")
        return 0
    
    except Exception as e:
        # Log failure
        logger.error(f"ETL process failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())