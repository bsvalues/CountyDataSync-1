#!/usr/bin/env python3
"""
Standalone executable for CountyDataSync ETL process.

This script is the entry point for the PyInstaller-packaged executable.
It handles the ETL process for county parcel data synchronization.

Usage:
    CountyDataSync [options]

Options:
    --batch-size NUMBER  Size of batches for data extraction (default: 1000)
    --output-dir PATH    Directory for output files (default: output)
    --test-data          Use test data instead of SQL Server
    --verbose            Enable verbose logging
    --config PATH        Path to custom configuration file
    --help               Show this help message and exit
"""
import os
import sys
import time
import argparse
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure basic logging before imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CountyDataSync')

def get_application_path() -> str:
    """Get the path of the application."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def configure_logging(verbose: bool = False, log_dir: Optional[str] = None) -> None:
    """Configure logging with file handler."""
    # Determine log directory
    if log_dir is None:
        app_path = get_application_path()
        log_dir = os.path.join(app_path, 'logs')
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Set log level
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'etl_process_{timestamp}.log')
    
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info(f"Logging to file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='CountyDataSync ETL Process')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Size of batches for data extraction (default: 1000)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory for output files (default: output)')
    parser.add_argument('--test-data', action='store_true',
                        help='Use test data instead of SQL Server')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--config', type=str,
                        help='Path to custom configuration file')
    return parser.parse_args()

def configure_environment(args: argparse.Namespace) -> None:
    """Configure environment based on command-line arguments."""
    # Set environment variables based on arguments
    if args.test_data:
        os.environ['USE_TEST_DATA'] = 'true'
        logger.info("Using test data instead of SQL Server")
    
    # Load custom configuration if provided
    if args.config and os.path.exists(args.config):
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(args.config)
            
            # Set environment variables from config
            if 'Database' in config:
                if 'MSSQL_SERVER' in config['Database']:
                    os.environ['MSSQL_SERVER'] = config['Database']['MSSQL_SERVER']
                if 'MSSQL_DATABASE' in config['Database']:
                    os.environ['MSSQL_DATABASE'] = config['Database']['MSSQL_DATABASE']
                if 'MSSQL_USERNAME' in config['Database']:
                    os.environ['MSSQL_USERNAME'] = config['Database']['MSSQL_USERNAME']
                if 'MSSQL_PASSWORD' in config['Database']:
                    os.environ['MSSQL_PASSWORD'] = config['Database']['MSSQL_PASSWORD']
                if 'DATABASE_URL' in config['Database']:
                    os.environ['DATABASE_URL'] = config['Database']['DATABASE_URL']
            
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {output_dir.absolute()}")

def run_etl_process(batch_size: int = 1000, output_dir: str = 'output') -> Dict[str, Any]:
    """
    Run the ETL process.
    
    Args:
        batch_size: Size of batches for data extraction
        output_dir: Directory for output files
        
    Returns:
        Dictionary with results and paths to output files
    """
    try:
        # Detect if running as packaged executable
        if getattr(sys, 'frozen', False):
            # When running as executable, Python's import system works differently
            # We need to set up the Python path to find our modules
            app_path = get_application_path()
            if app_path not in sys.path:
                sys.path.insert(0, app_path)
        
        # Import ETL modules (delayed import to ensure path is set up)
        try:
            # First try using the standalone module
            from etl.sync import run_etl
        except ImportError:
            # If standalone module not found, try the web app module
            logger.warning("Standalone ETL module not found, trying web app module.")
            from app import run_etl
        
        # Run the ETL process
        logger.info(f"Starting ETL process with batch size {batch_size}")
        start_time = time.time()
        
        result = run_etl(batch_size=batch_size, output_dir=output_dir)
        
        elapsed_time = time.time() - start_time
        logger.info(f"ETL process completed in {elapsed_time:.2f} seconds")
        
        # Log output files
        for key, path in result.items():
            if isinstance(path, str) and os.path.exists(path):
                size_kb = os.path.getsize(path) / 1024
                logger.info(f"  - {key}: {path} ({size_kb:.2f} KB)")
        
        return result
    
    except ImportError as e:
        logger.error(f"Failed to import ETL modules: {e}")
        logger.error(f"System path: {sys.path}")
        raise
    except Exception as e:
        logger.error(f"Error in ETL process: {e}")
        logger.error(traceback.format_exc())
        raise

def display_summary(result: Dict[str, Any]) -> None:
    """Display a summary of the ETL process results."""
    print("\n" + "=" * 40)
    print(" CountyDataSync ETL Process Summary ")
    print("=" * 40 + "\n")
    
    if not result:
        print("ETL process did not return any results.")
        return
    
    # Print output files
    print("Output Files:")
    for key, path in result.items():
        if isinstance(path, str) and os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  - {key}: {path} ({size_kb:.2f} KB)")
    
    # Print metrics if available
    if 'metrics' in result:
        print("\nPerformance Metrics:")
        metrics = result['metrics']
        for key, value in metrics.items():
            print(f"  - {key}: {value}")
    
    print("\nETL process completed successfully.")
    print("=" * 40 + "\n")

def main() -> int:
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure logging
    configure_logging(args.verbose)
    
    # Show application banner
    print("\n" + "=" * 40)
    print(" CountyDataSync ETL Process ")
    print("=" * 40 + "\n")
    
    try:
        # Configure environment
        configure_environment(args)
        
        # Run the ETL process
        result = run_etl_process(
            batch_size=args.batch_size,
            output_dir=args.output_dir
        )
        
        # Display summary
        display_summary(result)
        
        logger.info("ETL process completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        print(f"\nERROR: {e}")
        print("See log file for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())