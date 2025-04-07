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
from etl.utils import get_memory_usage, format_elapsed_time

logger = logging.getLogger(__name__)

def run_etl(batch_size=1000):
    """
    Run the full ETL process.
    
    Args:
        batch_size (int): Size of batches for data extraction
        
    Returns:
        dict: Dictionary with paths to the created output files
    """
    start_time = time.time()
    logger.info("Starting ETL process")
    logger.info(f"Current memory usage: {get_memory_usage()}")
    
    try:
        # Step 1: Extract data from SQL Server
        extraction_start = time.time()
        df = extract_data(batch_size=batch_size)
        
        if df.empty:
            logger.warning("No data extracted. ETL process will create empty output files.")
        else:
            logger.info(f"Extracted {len(df)} records in {format_elapsed_time(extraction_start)}")
        
        logger.info(f"Memory usage after extraction: {get_memory_usage()}")
        
        # Step 2: Transform data
        transformation_start = time.time()
        gdf = transform_data(df)
        logger.info(f"Transformation completed in {format_elapsed_time(transformation_start)}")
        logger.info(f"Memory usage after transformation: {get_memory_usage()}")
        
        # Step 3: Prepare data for different target databases
        stats_df = prepare_stats_data(gdf)
        working_df = prepare_working_data(gdf)
        
        # Step 4: Load data into target databases
        loading_start = time.time()
        
        # Create and load Geo DB
        geo_db_path = load_geo_db(gdf)
        
        # Create and load Stats DB
        stats_db_path = create_stats_db()
        load_stats_data(stats_df)
        
        # Create and load Working DB
        working_db_path = create_working_db()
        load_working_data(working_df)
        
        logger.info(f"Loading completed in {format_elapsed_time(loading_start)}")
        logger.info(f"Memory usage after loading: {get_memory_usage()}")
        
        # Return paths to created files
        output_files = {
            'geo_db': geo_db_path,
            'stats_db': stats_db_path,
            'working_db': working_db_path
        }
        
        total_time = time.time() - start_time
        logger.info(f"ETL process completed successfully in {format_elapsed_time(start_time)}")
        
        return output_files
        
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}", exc_info=True)
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
