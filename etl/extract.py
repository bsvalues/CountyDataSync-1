"""
Data extraction module for CountyDataSync ETL process.
Responsible for connecting to SQL Server and extracting data from MasterParcels table.
Also provides functionality to use test data when SQL Server is not available.
"""
import os
import logging
import pandas as pd
from config import SQL_SERVER_CONFIG, USE_TEST_DATA, TEST_DATA_RECORD_COUNT

# Try to import pyodbc, but handle the case where it's not available
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logging.warning("pyodbc not available, SQL Server connection will not be possible. Test data will be used instead.")

logger = logging.getLogger(__name__)

def create_connection():
    """
    Create and return a connection to the SQL Server database.
    
    Returns:
        pyodbc.Connection: Connection to the SQL Server database.
    """
    try:
        # Build connection string
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"DATABASE={SQL_SERVER_CONFIG['database']};"
            f"UID={SQL_SERVER_CONFIG['username']};"
            f"PWD={SQL_SERVER_CONFIG['password']}"
        )
        logger.debug(f"Connecting to SQL Server: {SQL_SERVER_CONFIG['server']}/{SQL_SERVER_CONFIG['database']}")
        
        # Create connection
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        logger.error(f"Failed to connect to SQL Server: {str(e)}")
        raise

def use_test_data(record_count=100):
    """
    Use test data instead of connecting to SQL Server.
    
    Args:
        record_count (int): Number of test records to generate
        
    Returns:
        pd.DataFrame: Test data
    """
    from etl.test_data import generate_test_parcel_data
    
    logger.info(f"Generating {record_count} test parcel records")
    test_df = generate_test_parcel_data(count=record_count)
    
    # Map test data columns to expected schema
    # Our extract normally returns: id, owner, use_code, acres, assessed_value, geometry
    mapped_df = pd.DataFrame({
        'id': test_df['ParcelID'],
        'owner': test_df['Address'],  # Use address as proxy for owner
        'use_code': test_df['LandUse'],
        'acres': test_df['Acres'],
        'assessed_value': test_df['AssessedValue'],
        'geometry': test_df['geometry']  # This is already in WKT format
    })
    
    logger.info(f"Generated {len(mapped_df)} test records")
    return mapped_df

def extract_data(batch_size=1000):
    """
    Extract data from MasterParcels table in SQL Server.
    Uses batch processing to handle large datasets.
    Falls back to test data if SQL Server is not available or USE_TEST_DATA is set.
    
    Args:
        batch_size (int): Number of records to fetch in each batch.
        
    Returns:
        pd.DataFrame: Extracted data.
    """
    # Check if we should use test data
    if USE_TEST_DATA or not PYODBC_AVAILABLE:
        logger.info("Using test data instead of connecting to SQL Server")
        return use_test_data(record_count=TEST_DATA_RECORD_COUNT)
    
    logger.info("Extracting data from MasterParcels table")
    
    try:
        conn = create_connection()
        
        # Query to fetch data in batches
        query = """
            SELECT id, owner, use_code, acres, assessed_value, geometry
            FROM MasterParcels
            ORDER BY id
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        offset = 0
        all_batches = []
        
        # Fetch data in batches
        while True:
            logger.debug(f"Fetching batch with offset {offset} and size {batch_size}")
            df_batch = pd.read_sql(query, conn, params=[offset, batch_size])
            
            if df_batch.empty:
                break
                
            all_batches.append(df_batch)
            offset += batch_size
            logger.debug(f"Fetched batch with {len(df_batch)} records")
        
        conn.close()
        
        # Combine all batches into a single DataFrame
        if all_batches:
            full_df = pd.concat(all_batches, ignore_index=True)
            logger.info(f"Total records fetched: {len(full_df)}")
            return full_df
        else:
            logger.warning("No data fetched from MasterParcels table")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Data extraction failed: {str(e)}")
        logger.info("Falling back to test data")
        return use_test_data(record_count=TEST_DATA_RECORD_COUNT)

def get_test_data_schema():
    """
    Get schema information for test data.
    
    Returns:
        pd.DataFrame: Schema information for test data.
    """
    # Sample schema based on our test data structure
    schema_data = [
        ('id', 'INT', None, 'NO'),
        ('owner', 'VARCHAR', 255, 'YES'),
        ('use_code', 'VARCHAR', 50, 'YES'),
        ('acres', 'FLOAT', None, 'YES'),
        ('assessed_value', 'DECIMAL', None, 'YES'),
        ('geometry', 'VARCHAR', -1, 'YES')  # WKT format
    ]
    
    schema_df = pd.DataFrame(schema_data, columns=['column_name', 'data_type', 'max_length', 'is_nullable'])
    return schema_df

def get_table_schema():
    """
    Get schema information for the MasterParcels table.
    Falls back to test data schema if SQL Server is not available.
    
    Returns:
        pd.DataFrame: Table schema information.
    """
    # Check if we should use test data
    if USE_TEST_DATA or not PYODBC_AVAILABLE:
        logger.info("Using test data schema instead of querying SQL Server")
        return get_test_data_schema()
    
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Query to get column information
        cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'MasterParcels'")
        
        # Fetch all rows
        schema_data = cursor.fetchall()
        
        # Create DataFrame from results
        schema_df = pd.DataFrame(schema_data, columns=['column_name', 'data_type', 'max_length', 'is_nullable'])
        
        cursor.close()
        conn.close()
        
        return schema_df
        
    except Exception as e:
        logger.error(f"Failed to get table schema: {str(e)}")
        logger.info("Falling back to test data schema")
        return get_test_data_schema()

if __name__ == "__main__":
    # Test the extraction process
    logging.basicConfig(level=logging.DEBUG)
    df = extract_data(batch_size=100)
    print(df.head())
    print(f"Total records: {len(df)}")
