"""
Delta synchronization module for CountyDataSync ETL process.
Provides functionality for incremental updates to the databases.
"""
import os
import time
import logging
import pandas as pd
import geopandas as gpd
import sqlite3
import hashlib
from datetime import datetime

from etl.utils import get_timestamp, ensure_directory_exists

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/delta_sync.log'
)
logger = logging.getLogger(__name__)

class DeltaSync:
    """
    Class for handling delta-based ETL updates
    """
    def __init__(self, source_connection=None, working_db=None):
        """
        Initialize DeltaSync instance
        
        Args:
            source_connection: Connection to the source database
            working_db (str): Path to the working database
        """
        self.source_connection = source_connection
        self.working_db = working_db or 'output/working_db.sqlite'
        self.change_log = []
        
    def calculate_hash(self, record):
        """
        Calculate a hash value for a record to detect changes
        
        Args:
            record (dict): Record to hash
            
        Returns:
            str: Hash value for the record
        """
        # Create a sorted string representation of the record, excluding geometry
        # which is handled separately
        record_copy = record.copy()
        if 'geometry' in record_copy:
            del record_copy['geometry']
            
        # Create a string with keys and values in sorted order
        record_str = ''.join([f"{k}:{record_copy[k]}" for k in sorted(record_copy.keys())])
        
        # Generate MD5 hash
        return hashlib.md5(record_str.encode()).hexdigest()
    
    def get_last_sync_info(self):
        """
        Get information about the last synchronization
        
        Returns:
            dict: Last sync information (timestamp, record count)
        """
        if not os.path.exists(self.working_db):
            return None
            
        try:
            conn = sqlite3.connect(self.working_db)
            cursor = conn.cursor()
            
            # Check if sync_metadata table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_metadata'")
            if not cursor.fetchone():
                return None
                
            # Get the latest sync info
            cursor.execute("SELECT * FROM sync_metadata ORDER BY sync_timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                return {
                    'sync_id': row[0],
                    'sync_timestamp': row[1],
                    'record_count': row[2],
                    'added_records': row[3],
                    'updated_records': row[4],
                    'deleted_records': row[5]
                }
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting last sync info: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def initialize_working_db(self):
        """
        Initialize the working database with required tables if they don't exist
        
        Returns:
            bool: True if successful, False otherwise
        """
        ensure_directory_exists(os.path.dirname(self.working_db))
        
        try:
            conn = sqlite3.connect(self.working_db)
            cursor = conn.cursor()
            
            # Create sync_metadata table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_metadata (
                sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_timestamp TEXT NOT NULL,
                record_count INTEGER,
                added_records INTEGER,
                updated_records INTEGER,
                deleted_records INTEGER
            )
            ''')
            
            # Create record_hashes table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS record_hashes (
                parcel_id TEXT PRIMARY KEY,
                hash_value TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error initializing working DB: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_current_record_hashes(self):
        """
        Get current record hashes from the working database
        
        Returns:
            dict: Dictionary of parcel_id to hash value
        """
        hashes = {}
        
        if not os.path.exists(self.working_db):
            return hashes
            
        try:
            conn = sqlite3.connect(self.working_db)
            cursor = conn.cursor()
            
            # Check if record_hashes table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='record_hashes'")
            if not cursor.fetchone():
                return hashes
                
            # Get all record hashes
            cursor.execute("SELECT parcel_id, hash_value FROM record_hashes")
            rows = cursor.fetchall()
            
            for row in rows:
                hashes[row[0]] = row[1]
                
            return hashes
        except sqlite3.Error as e:
            logger.error(f"Error getting record hashes: {str(e)}")
            return hashes
        finally:
            if conn:
                conn.close()
    
    def update_record_hashes(self, new_hashes):
        """
        Update record hashes in the working database
        
        Args:
            new_hashes (dict): Dictionary of parcel_id to hash value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.working_db)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            # Update record hashes
            for parcel_id, hash_value in new_hashes.items():
                cursor.execute('''
                INSERT OR REPLACE INTO record_hashes (parcel_id, hash_value, last_updated)
                VALUES (?, ?, ?)
                ''', (parcel_id, hash_value, timestamp))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating record hashes: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def record_sync_metadata(self, record_count, added, updated, deleted):
        """
        Record metadata about the current synchronization
        
        Args:
            record_count (int): Total record count
            added (int): Number of added records
            updated (int): Number of updated records
            deleted (int): Number of deleted records
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.working_db)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
            INSERT INTO sync_metadata (sync_timestamp, record_count, added_records, updated_records, deleted_records)
            VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, record_count, added, updated, deleted))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording sync metadata: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def identify_changes(self, df):
        """
        Identify changes between the current data and the stored data
        
        Args:
            df (pd.DataFrame): DataFrame with current data
            
        Returns:
            tuple: (added_records, updated_records, unchanged_records, deleted_record_ids)
        """
        # Initialize
        added_records = []
        updated_records = []
        unchanged_records = []
        
        # Get current record hashes
        current_hashes = self.get_current_record_hashes()
        
        # Calculate new hashes for all records
        new_hashes = {}
        for _, row in df.iterrows():
            parcel_id = str(row['parcel_id'])
            record_hash = self.calculate_hash(row.to_dict())
            new_hashes[parcel_id] = record_hash
            
            if parcel_id not in current_hashes:
                added_records.append(row)
                self.change_log.append({
                    'action': 'add',
                    'parcel_id': parcel_id,
                    'timestamp': datetime.now().isoformat()
                })
            elif current_hashes[parcel_id] != record_hash:
                updated_records.append(row)
                self.change_log.append({
                    'action': 'update',
                    'parcel_id': parcel_id,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                unchanged_records.append(row)
        
        # Identify deleted records
        deleted_record_ids = [
            parcel_id for parcel_id in current_hashes
            if parcel_id not in new_hashes
        ]
        
        for parcel_id in deleted_record_ids:
            self.change_log.append({
                'action': 'delete',
                'parcel_id': parcel_id,
                'timestamp': datetime.now().isoformat()
            })
        
        # Update record hashes in the working DB
        self.update_record_hashes(new_hashes)
        
        # Record sync metadata
        self.record_sync_metadata(
            record_count=len(df),
            added=len(added_records),
            updated=len(updated_records),
            deleted=len(deleted_record_ids)
        )
        
        return (
            pd.DataFrame(added_records) if added_records else pd.DataFrame(),
            pd.DataFrame(updated_records) if updated_records else pd.DataFrame(),
            pd.DataFrame(unchanged_records) if unchanged_records else pd.DataFrame(),
            deleted_record_ids
        )
    
    def save_change_log(self, output_dir='logs'):
        """
        Save the change log to a file
        
        Args:
            output_dir (str): Directory to save the change log
            
        Returns:
            str: Path to the change log file
        """
        ensure_directory_exists(output_dir)
        
        timestamp = get_timestamp()
        log_file = os.path.join(output_dir, f'delta_changes_{timestamp}.json')
        
        pd.DataFrame(self.change_log).to_json(log_file, orient='records', indent=2)
        
        return log_file
    
    def update_geo_db(self, gdf, geo_db_path, added, updated, deleted_ids):
        """
        Update the GeoPackage with delta changes
        
        Args:
            gdf (gpd.GeoDataFrame): Original GeoDataFrame
            geo_db_path (str): Path to the GeoPackage
            added (pd.DataFrame): Added records
            updated (pd.DataFrame): Updated records
            deleted_ids (list): List of deleted record IDs
            
        Returns:
            str: Path to the updated GeoPackage
        """
        # If the GeoPackage doesn't exist, create it with the full dataset
        if not os.path.exists(geo_db_path):
            logger.info(f"GeoPackage does not exist, creating new one at {geo_db_path}")
            gdf.to_file(geo_db_path, driver="GPKG")
            return geo_db_path
        
        try:
            # Read the existing GeoPackage
            existing_gdf = gpd.read_file(geo_db_path)
            
            # Handle deleted records
            if deleted_ids:
                logger.info(f"Removing {len(deleted_ids)} deleted records from GeoPackage")
                existing_gdf = existing_gdf[~existing_gdf['parcel_id'].astype(str).isin(deleted_ids)]
            
            # Convert added records to GeoDataFrame if not empty
            if not added.empty:
                logger.info(f"Adding {len(added)} new records to GeoPackage")
                # Ensure geometry column is properly set for the added records
                if 'geometry' in added.columns:
                    added_gdf = gpd.GeoDataFrame(added, geometry='geometry', crs=gdf.crs)
                    # Append to existing
                    existing_gdf = pd.concat([existing_gdf, added_gdf], ignore_index=True)
            
            # Update changed records
            if not updated.empty:
                logger.info(f"Updating {len(updated)} modified records in GeoPackage")
                # Convert to GeoDataFrame if needed
                if 'geometry' in updated.columns:
                    updated_gdf = gpd.GeoDataFrame(updated, geometry='geometry', crs=gdf.crs)
                    
                    # Remove the old versions of these records
                    updated_ids = updated_gdf['parcel_id'].astype(str).tolist()
                    existing_gdf = existing_gdf[~existing_gdf['parcel_id'].astype(str).isin(updated_ids)]
                    
                    # Add the updated records
                    existing_gdf = pd.concat([existing_gdf, updated_gdf], ignore_index=True)
            
            # Save the updated GeoDataFrame back to the GeoPackage
            existing_gdf.to_file(geo_db_path, driver="GPKG")
            
            return geo_db_path
        except Exception as e:
            logger.error(f"Error updating GeoPackage: {str(e)}")
            # If update fails, back up the original and create a new one
            backup_path = f"{geo_db_path}.backup_{get_timestamp()}"
            if os.path.exists(geo_db_path):
                os.rename(geo_db_path, backup_path)
                logger.warning(f"Failed to update GeoPackage, original backed up to {backup_path}")
            
            gdf.to_file(geo_db_path, driver="GPKG")
            return geo_db_path
    
    def update_stats_db(self, stats_df, stats_db_path, added, updated, deleted_ids):
        """
        Update the stats database with delta changes
        
        Args:
            stats_df (pd.DataFrame): Original stats DataFrame
            stats_db_path (str): Path to the stats database
            added (pd.DataFrame): Added records
            updated (pd.DataFrame): Updated records
            deleted_ids (list): List of deleted record IDs
            
        Returns:
            str: Path to the updated stats database
        """
        from etl.transform import prepare_stats_data
        
        # If the stats DB doesn't exist, create it with the full dataset
        if not os.path.exists(stats_db_path):
            logger.info(f"Stats DB does not exist, creating new one at {stats_db_path}")
            conn = sqlite3.connect(stats_db_path)
            stats_df.to_sql('parcel_stats', conn, if_exists='replace', index=False)
            conn.close()
            return stats_db_path
            
        try:
            conn = sqlite3.connect(stats_db_path)
            
            # Handle deleted records
            if deleted_ids:
                logger.info(f"Removing {len(deleted_ids)} deleted records from stats DB")
                placeholders = ', '.join(['?' for _ in deleted_ids])
                conn.execute(f"DELETE FROM parcel_stats WHERE parcel_id IN ({placeholders})", deleted_ids)
            
            # Handle added records
            if not added.empty:
                logger.info(f"Adding {len(added)} new records to stats DB")
                # Prepare stats data for the added records
                added_stats = prepare_stats_data(added)
                added_stats.to_sql('parcel_stats', conn, if_exists='append', index=False)
            
            # Handle updated records
            if not updated.empty:
                logger.info(f"Updating {len(updated)} modified records in stats DB")
                # Prepare stats data for the updated records
                updated_stats = prepare_stats_data(updated)
                
                # Delete the old versions of these records
                updated_ids = updated_stats['parcel_id'].astype(str).tolist()
                placeholders = ', '.join(['?' for _ in updated_ids])
                conn.execute(f"DELETE FROM parcel_stats WHERE parcel_id IN ({placeholders})", updated_ids)
                
                # Insert the updated records
                updated_stats.to_sql('parcel_stats', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            return stats_db_path
            
        except sqlite3.Error as e:
            logger.error(f"Error updating stats DB: {str(e)}")
            # If update fails, back up the original and create a new one
            backup_path = f"{stats_db_path}.backup_{get_timestamp()}"
            if os.path.exists(stats_db_path):
                os.rename(stats_db_path, backup_path)
                logger.warning(f"Failed to update stats DB, original backed up to {backup_path}")
            
            conn = sqlite3.connect(stats_db_path)
            stats_df.to_sql('parcel_stats', conn, if_exists='replace', index=False)
            conn.close()
            return stats_db_path
            
    def run_delta_sync(self, df, gdf, stats_df, geo_db_path, stats_db_path):
        """
        Run a delta sync operation
        
        Args:
            df (pd.DataFrame): Current data
            gdf (gpd.GeoDataFrame): Current GeoDataFrame
            stats_df (pd.DataFrame): Current stats DataFrame
            geo_db_path (str): Path to the GeoPackage
            stats_db_path (str): Path to the stats database
            
        Returns:
            dict: Delta sync results
        """
        start_time = time.time()
        
        # Initialize working DB if needed
        if not self.initialize_working_db():
            logger.error("Failed to initialize working DB")
            return {
                'success': False,
                'error': 'Failed to initialize working DB'
            }
        
        # Identify changes
        added, updated, unchanged, deleted_ids = self.identify_changes(df)
        
        # Update GeoPackage
        geo_db_path = self.update_geo_db(
            gdf, geo_db_path, 
            added=added if not added.empty else pd.DataFrame(),
            updated=updated if not updated.empty else pd.DataFrame(),
            deleted_ids=deleted_ids
        )
        
        # Update Stats DB
        stats_db_path = self.update_stats_db(
            stats_df, stats_db_path,
            added=added if not added.empty else pd.DataFrame(),
            updated=updated if not updated.empty else pd.DataFrame(),
            deleted_ids=deleted_ids
        )
        
        # Save change log
        change_log_path = self.save_change_log()
        
        elapsed_time = time.time() - start_time
        
        return {
            'success': True,
            'geo_db_path': geo_db_path,
            'stats_db_path': stats_db_path,
            'working_db_path': self.working_db,
            'change_log_path': change_log_path,
            'added_records': len(added),
            'updated_records': len(updated),
            'unchanged_records': len(unchanged),
            'deleted_records': len(deleted_ids),
            'elapsed_time': elapsed_time
        }