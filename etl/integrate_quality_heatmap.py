"""
Integration module for the Interactive Data Quality Heatmap.

This module integrates the data quality analyzer with the ETL process,
allowing it to be triggered after successful ETL jobs to generate
quality metrics and heatmap visualizations.
"""
import os
import logging
import pandas as pd
from datetime import datetime
from etl.data_quality import DataQualityAnalyzer
from etl.utils import ensure_directory_exists, get_timestamp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/data_quality.log'
)
logger = logging.getLogger(__name__)

def analyze_etl_output(job, output_dir='output'):
    """
    Analyze the quality of data in an ETL job's output.
    
    Args:
        job: ETLJob instance
        output_dir (str): Directory to save quality reports
        
    Returns:
        dict: Paths to the generated reports, or None if analysis fails
    """
    logger.info(f"Starting data quality analysis for job {job.id}: {job.job_name}")
    
    # Create job-specific output directory
    job_output_dir = os.path.join(output_dir, f"job_{job.id}")
    ensure_directory_exists(job_output_dir)
    
    # Determine the data source based on job information
    data = None
    
    try:
        # If the job has a working DB path, try to extract data from there
        if job.working_db_path and os.path.exists(job.working_db_path):
            import sqlite3
            conn = sqlite3.connect(job.working_db_path)
            # Try to get data from the parcels table (or another main data table)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if 'parcels' in tables['name'].values:
                data = pd.read_sql_query("SELECT * FROM parcels", conn)
            elif len(tables) > 0:
                # Get data from the first table
                table_name = tables['name'].iloc[0]
                data = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
        
        # If no data yet and the job has a source file, try to read that
        if data is None and job.source_file and os.path.exists(job.source_file):
            file_ext = os.path.splitext(job.source_file)[1].lower()
            if file_ext == '.csv':
                data = pd.read_csv(job.source_file)
            elif file_ext in ['.xls', '.xlsx']:
                data = pd.read_excel(job.source_file)
        
        # If still no data, look for output CSV files
        if data is None:
            csv_files = []
            if job.stats_db_path:
                csv_dir = os.path.dirname(job.stats_db_path)
                csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
                
            if csv_files:
                data = pd.read_csv(os.path.join(csv_dir, csv_files[0]))
        
        # If we have data, analyze it
        if data is not None and not data.empty:
            analyzer = DataQualityAnalyzer(output_dir=job_output_dir)
            report_paths = analyzer.generate_quality_report(
                data, 
                report_name=f"job_{job.id}_quality"
            )
            
            logger.info(f"Data quality analysis completed for job {job.id}. Reports saved to: {job_output_dir}")
            return report_paths
        else:
            logger.warning(f"No data found for job {job.id}. Cannot perform quality analysis.")
            return None
    
    except Exception as e:
        logger.error(f"Error performing data quality analysis for job {job.id}: {str(e)}")
        return None


def analyze_all_completed_jobs(jobs, output_dir='output'):
    """
    Analyze data quality for all completed ETL jobs that haven't been analyzed yet.
    
    Args:
        jobs: List of ETLJob instances
        output_dir (str): Directory to save quality reports
        
    Returns:
        list: List of job IDs that were successfully analyzed
    """
    logger.info(f"Starting data quality analysis for {len(jobs)} jobs")
    analyzed_jobs = []
    
    for job in jobs:
        try:
            # Only analyze completed jobs
            if job.status != 'completed':
                continue
                
            # Check if this job has already been analyzed
            job_output_dir = os.path.join(output_dir, f"job_{job.id}")
            if os.path.exists(job_output_dir) and len(os.listdir(job_output_dir)) > 0:
                # Job already has quality reports
                continue
                
            # Analyze the job
            report_paths = analyze_etl_output(job, output_dir)
            if report_paths:
                analyzed_jobs.append(job.id)
        
        except Exception as e:
            logger.error(f"Error analyzing job {job.id}: {str(e)}")
    
    logger.info(f"Data quality analysis complete. Analyzed {len(analyzed_jobs)} new jobs.")
    return analyzed_jobs