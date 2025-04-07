#!/usr/bin/env python
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
import logging
import time
import argparse
from datetime import datetime
from pathlib import Path
import uuid

# Setup logging before imports
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"etl_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger(__name__)

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("python-dotenv not found, skipping .env file loading")

# Ensure required directories exist
os.makedirs('output', exist_ok=True)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='CountyDataSync ETL Service')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for data extraction (default: 1000)')
    parser.add_argument('--test-data', action='store_true',
                        help='Use test data instead of connecting to SQL Server')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory for output files (default: output)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')
    
    return parser.parse_args()

def configure_environment(args):
    """Configure environment variables based on command line arguments."""
    if args.test_data:
        os.environ['USE_TEST_DATA'] = 'true'
        logger.info("Using test data (from command line argument)")
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    logger.info(f"Log level set to {args.log_level}")
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Output directory: {args.output_dir}")

def run_standalone_etl(batch_size=1000, output_dir='output'):
    """
    Run the ETL process in standalone mode.
    
    Args:
        batch_size (int): Size of batches for data extraction
        output_dir (str): Directory for output files
        
    Returns:
        dict: Dictionary with paths to the created output files and performance metrics
    """
    from etl.sync import run_etl
    
    # Generate a unique run ID
    run_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"Starting ETL process (Run ID: {run_id})")
    
    try:
        # Run the ETL process
        result = run_etl(batch_size=batch_size)
        
        # Log the results
        files = result.get('files', {})
        performance = result.get('performance', {})
        
        logger.info("ETL process completed successfully")
        logger.info(f"Output files:")
        for name, path in files.items():
            logger.info(f"  {name}: {path}")
        
        logger.info(f"Performance metrics:")
        for metric, value in performance.items():
            if 'time' in metric:
                logger.info(f"  {metric}: {value:.2f} seconds")
            elif metric == 'peak_memory_usage':
                logger.info(f"  {metric}: {value:.2f} MB")
            else:
                logger.info(f"  {metric}: {value}")
        
        return result
        
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}", exc_info=True)
        raise

def main():
    """Main entry point."""
    print("=" * 80)
    print("CountyDataSync ETL Service")
    print("=" * 80)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure environment based on arguments
    configure_environment(args)
    
    # Display environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Operating system: {sys.platform}")
    
    # Check for critical environment variables
    if 'DATABASE_URL' not in os.environ:
        logger.warning("DATABASE_URL environment variable not set")
    
    if os.environ.get('USE_TEST_DATA') != 'true' and (
        'MSSQL_SERVER' not in os.environ or
        'MSSQL_DATABASE' not in os.environ or
        'MSSQL_USERNAME' not in os.environ
    ):
        logger.warning("SQL Server connection environment variables not fully set. "
                      "Consider using --test-data if SQL Server is unavailable.")
    
    try:
        # Run the ETL process
        result = run_standalone_etl(batch_size=args.batch_size, output_dir=args.output_dir)
        
        print("\nETL process completed successfully!")
        print(f"Log file: {log_file}")
        
        # Display output file paths
        print("\nOutput files:")
        for name, path in result.get('files', {}).items():
            print(f"  {name}: {path}")
        
        # Format elapsed time
        elapsed = result.get('performance', {}).get('total_time', 0)
        minutes, seconds = divmod(elapsed, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            time_str = f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"
        elif minutes > 0:
            time_str = f"{int(minutes)}m {seconds:.2f}s"
        else:
            time_str = f"{seconds:.2f}s"
        
        print(f"\nTotal processing time: {time_str}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"\nERROR: ETL process failed. See log file for details: {log_file}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)