"""
Data transformation module for CountyDataSync ETL process.
Handles conversion of WKT to geometry and other data transformations.
"""
import logging
import pandas as pd
import geopandas as gpd
from shapely import wkt

logger = logging.getLogger(__name__)

def transform_data(df):
    """
    Transform the extracted data:
    - Convert WKT strings to shapely geometry objects
    - Create a GeoDataFrame
    
    Args:
        df (pd.DataFrame): DataFrame with a 'geometry' column containing WKT strings
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with properly typed geometry column
    """
    logger.info("Transforming data")
    
    try:
        # Make a copy to avoid modifying the original DataFrame
        df_copy = df.copy()
        
        # Check if DataFrame is empty
        if df_copy.empty:
            logger.warning("Empty DataFrame provided for transformation")
            return gpd.GeoDataFrame(geometry=gpd.GeoSeries(), crs='EPSG:4326')
        
        # Check if 'geometry' column exists
        if 'geometry' not in df_copy.columns:
            logger.error("No 'geometry' column found in the input DataFrame")
            raise ValueError("No 'geometry' column found in the input DataFrame")
            
        # Remove rows with null geometry
        null_geoms = df_copy['geometry'].isna()
        if null_geoms.any():
            logger.warning(f"Removing {null_geoms.sum()} rows with null geometry")
            df_copy = df_copy[~null_geoms]
            
        # Convert WKT strings to shapely geometries
        logger.debug("Converting WKT strings to shapely geometries")
        df_copy['geometry'] = df_copy['geometry'].apply(lambda x: wkt.loads(x) if x else None)
        
        # Convert DataFrame to GeoDataFrame
        logger.debug("Creating GeoDataFrame")
        gdf = gpd.GeoDataFrame(df_copy, geometry='geometry', crs='EPSG:4326')
        
        # Validate that the GeoDataFrame has valid geometries
        invalid_geoms = ~gdf.is_valid
        if invalid_geoms.any():
            logger.warning(f"Found {invalid_geoms.sum()} invalid geometries")
            # Attempt to fix invalid geometries
            gdf.loc[invalid_geoms, 'geometry'] = gdf.loc[invalid_geoms, 'geometry'].buffer(0)
            
        logger.info(f"Transformation complete. GeoDataFrame contains {len(gdf)} records")
        return gdf
        
    except Exception as e:
        logger.error(f"Data transformation failed: {str(e)}")
        raise

def prepare_stats_data(gdf):
    """
    Prepare data for the Stats DB by aggregating statistics.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame with parcel data
        
    Returns:
        pd.DataFrame: DataFrame with aggregated statistics
    """
    logger.info("Preparing statistics data")
    
    try:
        # Check if GeoDataFrame is empty
        if gdf.empty:
            logger.warning("Empty GeoDataFrame provided for stats preparation")
            return pd.DataFrame()
            
        # Extract relevant columns for stats
        stats_df = gdf[['id', 'use_code', 'acres', 'assessed_value']].copy()
        
        logger.info(f"Statistics data prepared with {len(stats_df)} records")
        return stats_df
        
    except Exception as e:
        logger.error(f"Stats data preparation failed: {str(e)}")
        raise

def prepare_working_data(gdf):
    """
    Prepare data for the Working DB.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame with parcel data
        
    Returns:
        pd.DataFrame: DataFrame for Working DB
    """
    logger.info("Preparing working data")
    
    try:
        # Check if GeoDataFrame is empty
        if gdf.empty:
            logger.warning("Empty GeoDataFrame provided for working data preparation")
            return pd.DataFrame()
            
        # Extract relevant columns for working data
        working_df = gdf[['id', 'owner', 'use_code']].copy()
        
        logger.info(f"Working data prepared with {len(working_df)} records")
        return working_df
        
    except Exception as e:
        logger.error(f"Working data preparation failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Test transformation with a simple DataFrame
    logging.basicConfig(level=logging.DEBUG)
    
    # Create a test DataFrame with WKT geometry
    test_df = pd.DataFrame({
        'id': [1, 2],
        'owner': ['Alice', 'Bob'],
        'use_code': ['RES', 'COM'],
        'acres': [1.5, 2.0],
        'assessed_value': [150000, 200000],
        'geometry': [
            'POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))',
            'POLYGON((2 2, 3 2, 3 3, 2 3, 2 2))'
        ]
    })
    
    # Transform the test data
    gdf = transform_data(test_df)
    print(gdf.head())
    
    # Prepare stats and working data
    stats_df = prepare_stats_data(gdf)
    working_df = prepare_working_data(gdf)
    
    print("\nStats DataFrame:")
    print(stats_df.head())
    
    print("\nWorking DataFrame:")
    print(working_df.head())
