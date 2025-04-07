"""
Integration module for CountyDataSync ETL process.
Combines extraction, transformation, and loading steps.
"""
import logging
import os
import time
from etl.extract import extract_data
from etl.transform import transform_data, prepare_stats_data, prepare_working_data
from etl.load import (
    load_geo_db, 
    create_stats_db, load_stats_data,
    create_working_db, load_working_data
)
from etl.utils import (
    get_memory_usage, 
    get_memory_usage_value, 
    get_cpu_usage, 
    format_elapsed_time
)

logger = logging.getLogger(__name__)

def run_etl(batch_size=1000, job_id=None):
    """
    Run the full ETL process.
    
    Args:
        batch_size (int): Size of batches for data extraction
        job_id (int): ID of the ETLJob record for this process
        
    Returns:
        dict: Dictionary with paths to the created output files and performance metrics
    """
    from app import db
    from models import ETLJob, PerformanceMetric
    
    # If job_id is provided, fetch the job
    job = None
    if job_id:
        job = ETLJob.query.get(job_id)
    
    start_time = time.time()
    logger.info("Starting ETL process")
    logger.info(f"Current memory usage: {get_memory_usage()}")
    
    # Initialize peak memory usage
    peak_memory = get_memory_usage_value()
    
    try:
        # Step 1: Extract data from SQL Server
        extraction_start = time.time()
        
        # Create performance metric record for extraction start
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='extraction',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=0,
                description="Starting extraction"
            )
            db.session.add(metric)
            db.session.commit()
        
        df = extract_data(batch_size=batch_size)
        extraction_time = time.time() - extraction_start
        
        # Update peak memory
        current_memory = get_memory_usage_value()
        peak_memory = max(peak_memory, current_memory)
        
        if df.empty:
            logger.warning("No data extracted. ETL process will create empty output files.")
            record_count = 0
        else:
            record_count = len(df)
            logger.info(f"Extracted {record_count} records in {format_elapsed_time(extraction_start)}")
        
        logger.info(f"Memory usage after extraction: {get_memory_usage()}")
        
        # Create performance metric record for extraction end
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='extraction',
                memory_usage=current_memory,
                cpu_usage=get_cpu_usage(),
                elapsed_time=extraction_time,
                records_processed=record_count,
                description="Extraction completed"
            )
            db.session.add(metric)
            db.session.commit()
        
        # Step 2: Transform data
        transformation_start = time.time()
        
        # Create performance metric record for transformation start
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='transformation',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=time.time() - start_time,
                description="Starting transformation"
            )
            db.session.add(metric)
            db.session.commit()
        
        gdf = transform_data(df)
        transformation_time = time.time() - transformation_start
        
        # Update peak memory
        current_memory = get_memory_usage_value()
        peak_memory = max(peak_memory, current_memory)
        
        logger.info(f"Transformation completed in {format_elapsed_time(transformation_start)}")
        logger.info(f"Memory usage after transformation: {get_memory_usage()}")
        
        # Create performance metric record for transformation end
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='transformation',
                memory_usage=current_memory,
                cpu_usage=get_cpu_usage(),
                elapsed_time=transformation_time,
                records_processed=record_count,
                description="Transformation completed"
            )
            db.session.add(metric)
            db.session.commit()
        
        # Step 3: Prepare data for different target databases
        stats_df = prepare_stats_data(gdf)
        working_df = prepare_working_data(gdf)
        
        # Step 4: Load data into target databases
        loading_start = time.time()
        
        # Create performance metric record for loading start
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='loading',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=time.time() - start_time,
                description="Starting loading"
            )
            db.session.add(metric)
            db.session.commit()
        
        # Create and load Geo DB
        geo_db_path = load_geo_db(gdf)
        
        # Create and load Stats DB
        stats_db_path = create_stats_db()
        load_stats_data(stats_df)
        
        # Create and load Working DB
        working_db_path = create_working_db()
        load_working_data(working_df)
        
        loading_time = time.time() - loading_start
        
        # Update peak memory
        current_memory = get_memory_usage_value()
        peak_memory = max(peak_memory, current_memory)
        
        logger.info(f"Loading completed in {format_elapsed_time(loading_start)}")
        logger.info(f"Memory usage after loading: {get_memory_usage()}")
        
        # Create performance metric record for loading end
        if job:
            metric = PerformanceMetric(
                job_id=job.id,
                stage='loading',
                memory_usage=current_memory,
                cpu_usage=get_cpu_usage(),
                elapsed_time=loading_time,
                records_processed=record_count,
                description="Loading completed"
            )
            db.session.add(metric)
            db.session.commit()
        
        # Return paths to created files
        output_files = {
            'geo_db': geo_db_path,
            'stats_db': stats_db_path,
            'working_db': working_db_path
        }
        
        total_time = time.time() - start_time
        logger.info(f"ETL process completed successfully in {format_elapsed_time(start_time)}")
        
        # Update job with performance metrics
        if job:
            job.extraction_time = extraction_time
            job.transformation_time = transformation_time
            job.loading_time = loading_time
            job.peak_memory_usage = peak_memory
            job.record_count = record_count
            db.session.commit()
        
        # Add performance metrics to output
        performance_metrics = {
            'extraction_time': extraction_time,
            'transformation_time': transformation_time,
            'loading_time': loading_time,
            'total_time': total_time,
            'peak_memory_usage': peak_memory,
            'record_count': record_count
        }
        
        output = {
            'files': output_files,
            'performance': performance_metrics
        }
        
        return output
        
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}", exc_info=True)
        
        # Record failure in job if available
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()
            
            # Create performance metric record for failure
            metric = PerformanceMetric(
                job_id=job.id,
                stage='failure',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=time.time() - start_time,
                description=f"Process failed: {str(e)}"
            )
            db.session.add(metric)
            db.session.commit()
            
        raise

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the ETL process
    output_files = run_etl()
    
    # Print the paths to the created files
    for name, path in output_files.items():
        print(f"{name}: {path}")
