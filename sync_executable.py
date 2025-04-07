#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import platform
import datetime


def get_application_path() -> str:
    """Get the path of the application."""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        app_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_path = os.path.dirname(os.path.abspath(__file__))
    return app_path


def configure_logging(verbose: bool = False, log_dir: Optional[str] = None) -> None:
    """Configure logging with file handler."""
    # Set the log level
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create the logs directory if it doesn't exist
    if log_dir is None:
        app_path = get_application_path()
        log_dir = os.path.join(app_path, 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f'etl_process_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Logging initialized. Log file: {log_file}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='CountyDataSync ETL Process',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Size of batches for data extraction'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory for output files'
    )
    
    parser.add_argument(
        '--test-data',
        action='store_true',
        help='Use test data instead of SQL Server'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration file'
    )
    
    return parser.parse_args()


def configure_environment(args: argparse.Namespace) -> None:
    """Configure environment based on command-line arguments."""
    # Set environment variables for testing
    if args.test_data:
        os.environ['USE_TEST_DATA'] = 'true'
        logging.info("Using test data mode")
    
    # Set output directory
    app_path = get_application_path()
    output_dir = os.path.join(app_path, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output directory: {output_dir}")
    
    # Load configuration if specified
    if args.config:
        if os.path.exists(args.config):
            # Load custom configuration
            from dotenv import load_dotenv
            load_dotenv(args.config)
            logging.info(f"Loaded configuration from {args.config}")
        else:
            logging.warning(f"Configuration file not found: {args.config}")
    else:
        # Load default .env if it exists
        env_path = os.path.join(app_path, '.env')
        if os.path.exists(env_path):
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logging.info(f"Loaded configuration from {env_path}")


def run_etl_process(batch_size: int = 1000, output_dir: str = 'output') -> Dict[str, Any]:
    """
    Run the ETL process.
    
    Args:
        batch_size: Size of batches for data extraction
        output_dir: Directory for output files
        
    Returns:
        Dictionary with results and paths to output files
    """
    logging.info("Starting ETL process")
    
    # Check if output directory exists, create if needed
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    start_time = time.time()
    
    try:
        # Import the ETL modules
        try:
            from etl.sync import run_etl_pipeline
            from etl.data_quality import analyze_parcel_data
        except ImportError:
            # If running as executable with bundled modules
            logging.info("Using bundled ETL modules")
            # This should work in the PyInstaller bundle
            from sync import run_etl_pipeline
            from data_quality import analyze_parcel_data
        
        # Run the ETL pipeline
        result = run_etl_pipeline(batch_size=batch_size, output_dir=output_dir)
        
        # Run data quality analysis
        if result.get('transformed_data') is not None:
            quality_results = analyze_parcel_data(result['transformed_data'], output_dir=output_dir)
            result['quality_report'] = quality_results
        
        end_time = time.time()
        result['execution_time'] = end_time - start_time
        
        logging.info(f"ETL process completed in {result['execution_time']:.2f} seconds")
        return result
    
    except Exception as e:
        logging.error(f"ETL process failed: {str(e)}", exc_info=True)
        end_time = time.time()
        return {
            'error': str(e),
            'execution_time': end_time - start_time,
            'status': 'failed'
        }


def display_summary(result: Dict[str, Any]) -> None:
    """Display a summary of the ETL process results."""
    print("\n" + "=" * 60)
    print("CountyDataSync ETL Process Summary")
    print("=" * 60)
    
    if 'error' in result:
        print(f"\nStatus: Failed")
        print(f"Error: {result['error']}")
    else:
        print(f"\nStatus: Completed")
    
    print(f"Execution Time: {result.get('execution_time', 0):.2f} seconds")
    
    if 'record_count' in result:
        print(f"Records Processed: {result['record_count']}")
    
    if 'output_files' in result:
        print("\nOutput Files:")
        for file_type, file_path in result['output_files'].items():
            print(f"  - {file_type}: {file_path}")
    
    if 'quality_report' in result:
        print("\nData Quality Report:")
        quality = result['quality_report']
        if 'overall_score' in quality:
            print(f"  Overall Quality Score: {quality['overall_score']:.2f}%")
        if 'completeness' in quality:
            print(f"  Completeness: {quality['completeness']:.2f}%")
        if 'validity' in quality:
            print(f"  Validity: {quality['validity']:.2f}%")
        if 'report_file' in quality:
            print(f"  Detailed Report: {quality['report_file']}")
    
    print("\n" + "=" * 60)


def main() -> int:
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure logging
    configure_logging(verbose=args.verbose)
    
    # Log system information
    logging.info(f"CountyDataSync ETL Process started")
    logging.info(f"Python version: {platform.python_version()}")
    logging.info(f"Platform: {platform.platform()}")
    
    # Configure environment
    configure_environment(args)
    
    # Run the ETL process
    result = run_etl_process(batch_size=args.batch_size, output_dir=args.output_dir)
    
    # Display summary
    display_summary(result)
    
    # Return exit code
    return 0 if 'error' not in result else 1


if __name__ == "__main__":
    sys.exit(main())