"""
Data extraction module for CountyDataSync ETL process.
Responsible for connecting to SQL Server and extracting data from MasterParcels table.
"""
import os
import logging
import pyodbc
import pandas as pd
from config import SQL_SERVER_CONFIG

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

def extract_data(batch_size=1000):
    """
    Extract data from MasterParcels table in SQL Server.
    Uses batch processing to handle large datasets.
    
    Args:
        batch_size (int): Number of records to fetch in each batch.
        
    Returns:
        pd.DataFrame: Extracted data.
    """
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
        raise

def get_table_schema():
    """
    Get schema information for the MasterParcels table.
    
    Returns:
        pd.DataFrame: Table schema information.
    """
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
        raise

if __name__ == "__main__":
    # Test the extraction process
    logging.basicConfig(level=logging.DEBUG)
    df = extract_data(batch_size=100)
    print(df.head())
    print(f"Total records: {len(df)}")
