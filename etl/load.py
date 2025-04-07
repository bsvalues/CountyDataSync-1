"""
Data loading module for CountyDataSync ETL process.
Handles loading data into the three target databases:
1. Geo DB: GeoPackage for spatial data
2. Stats DB: SQLite database for aggregated statistics
3. Working DB: SQLite database for temporary/editable data
"""
import os
import logging
import sqlite3
import pandas as pd
import geopandas as gpd
from config import OUTPUT_PATHS

logger = logging.getLogger(__name__)

def load_geo_db(gdf, output_file=None):
    """
    Load spatial data into a GeoPackage file.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame with spatial data
        output_file (str, optional): Path to output GeoPackage file
        
    Returns:
        str: Path to the created GeoPackage file
    """
    if output_file is None:
        output_file = OUTPUT_PATHS['geo_db']
        
    logger.info(f"Loading spatial data into GeoPackage: {output_file}")
    
    try:
        # Check if GeoDataFrame is empty
        if gdf.empty:
            logger.warning("Empty GeoDataFrame provided for Geo DB loading")
            # Create an empty GeoPackage
            empty_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(), crs='EPSG:4326')
            empty_gdf.to_file(output_file, driver='GPKG')
            logger.info(f"Created empty GeoPackage: {output_file}")
            return output_file
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Write to GeoPackage
        gdf.to_file(output_file, driver='GPKG')
        
        logger.info(f"GeoPackage created successfully at {output_file} with {len(gdf)} features")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to create GeoPackage: {str(e)}")
        raise

def create_stats_db(db_file=None):
    """
    Create the Stats SQLite database.
    
    Args:
        db_file (str, optional): Path to the SQLite database file
        
    Returns:
        str: Path to the created database file
    """
    if db_file is None:
        db_file = OUTPUT_PATHS['stats_db']
        
    logger.info(f"Creating Stats DB: {db_file}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        
        # Connect to SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                use_code TEXT,
                acres REAL,
                assessed_value REAL
            )
        ''')
        
        # Create index on use_code for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_code ON stats (use_code)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stats DB created at {db_file}")
        return db_file
        
    except Exception as e:
        logger.error(f"Failed to create Stats DB: {str(e)}")
        raise

def load_stats_data(df, db_file=None):
    """
    Load data into the Stats SQLite database.
    
    Args:
        df (pd.DataFrame): DataFrame with statistics data
        db_file (str, optional): Path to the SQLite database file
        
    Returns:
        str: Path to the database file
    """
    if db_file is None:
        db_file = OUTPUT_PATHS['stats_db']
        
    logger.info(f"Loading data into Stats DB: {db_file}")
    
    try:
        # Check if DataFrame is empty
        if df.empty:
            logger.warning("Empty DataFrame provided for Stats DB loading")
            return db_file
            
        # Connect to SQLite database
        conn = sqlite3.connect(db_file)
        
        # Write DataFrame to SQLite
        df.to_sql('stats', conn, if_exists='replace', index=False)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Data loaded into Stats DB: {len(df)} records")
        return db_file
        
    except Exception as e:
        logger.error(f"Failed to load data into Stats DB: {str(e)}")
        raise

def create_working_db(db_file=None):
    """
    Create the Working SQLite database.
    
    Args:
        db_file (str, optional): Path to the SQLite database file
        
    Returns:
        str: Path to the created database file
    """
    if db_file is None:
        db_file = OUTPUT_PATHS['working_db']
        
    logger.info(f"Creating Working DB: {db_file}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        
        # Connect to SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS working (
                id INTEGER PRIMARY KEY,
                owner TEXT,
                use_code TEXT
            )
        ''')
        
        # Create indices for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_owner ON working (owner)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_code ON working (use_code)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Working DB created at {db_file}")
        return db_file
        
    except Exception as e:
        logger.error(f"Failed to create Working DB: {str(e)}")
        raise

def load_working_data(df, db_file=None):
    """
    Load data into the Working SQLite database.
    
    Args:
        df (pd.DataFrame): DataFrame with working data
        db_file (str, optional): Path to the SQLite database file
        
    Returns:
        str: Path to the database file
    """
    if db_file is None:
        db_file = OUTPUT_PATHS['working_db']
        
    logger.info(f"Loading data into Working DB: {db_file}")
    
    try:
        # Check if DataFrame is empty
        if df.empty:
            logger.warning("Empty DataFrame provided for Working DB loading")
            return db_file
            
        # Connect to SQLite database
        conn = sqlite3.connect(db_file)
        
        # Write DataFrame to SQLite
        df.to_sql('working', conn, if_exists='replace', index=False)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Data loaded into Working DB: {len(df)} records")
        return db_file
        
    except Exception as e:
        logger.error(f"Failed to load data into Working DB: {str(e)}")
        raise

if __name__ == "__main__":
    # Test loading with sample data
    logging.basicConfig(level=logging.DEBUG)
    
    # Create test data
    from shapely.geometry import Polygon
    
    # Create a test GeoDataFrame
    geometry = [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]), Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])]
    gdf = gpd.GeoDataFrame({
        'id': [1, 2],
        'owner': ['Alice', 'Bob'],
        'use_code': ['RES', 'COM'],
        'acres': [1.5, 2.0],
        'assessed_value': [150000, 200000]
    }, geometry=geometry, crs='EPSG:4326')
    
    # Create test DataFrames for Stats and Working DBs
    stats_df = pd.DataFrame({
        'id': [1, 2],
        'use_code': ['RES', 'COM'],
        'acres': [1.5, 2.0],
        'assessed_value': [150000, 200000]
    })
    
    working_df = pd.DataFrame({
        'id': [1, 2],
        'owner': ['Alice', 'Bob'],
        'use_code': ['RES', 'COM']
    })
    
    # Test loading into each database
    geo_db_path = load_geo_db(gdf, 'test_geo.gpkg')
    
    stats_db_path = create_stats_db('test_stats.sqlite')
    load_stats_data(stats_df, stats_db_path)
    
    working_db_path = create_working_db('test_working.sqlite')
    load_working_data(working_df, working_db_path)
    
    print(f"Test files created: {geo_db_path}, {stats_db_path}, {working_db_path}")
