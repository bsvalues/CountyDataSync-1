# CountyDataSync Standalone Installer Guide

This guide explains how to install and use the CountyDataSync standalone executable for your ETL processes.

## Prerequisites

- Windows 10/11, macOS, or Linux
- Internet connection (for first-time setup only)
- Access credentials to your SQL Server database (if using real data)

## Installation Steps

1. **Download the Executable**

   Download the appropriate executable for your operating system:
   - Windows: `CountyDataSync.exe`
   - macOS/Linux: `CountyDataSync`

2. **Create Configuration File**

   Create a `.env` file in the same directory as the executable with the following configurations:

   ```
   # SQL Server connection settings (if using real data)
   SQL_SERVER_HOST=your_sql_server_host
   SQL_DATABASE=your_database_name
   SQL_USERNAME=your_username
   SQL_PASSWORD=your_password
   SQL_DRIVER={ODBC Driver 17 for SQL Server}

   # Output settings
   OUTPUT_DIR=output
   GEO_DB_NAME=geo_db.gpkg
   STATS_DB_NAME=stats_db.sqlite
   WORKING_DB_NAME=working_db.sqlite

   # Batch settings
   DEFAULT_BATCH_SIZE=1000

   # Logging settings
   LOG_LEVEL=INFO
   LOG_FILE=etl_process.log

   # CRS settings
   DEFAULT_CRS=EPSG:4326

   # Performance settings
   MAX_MEMORY_USAGE_MB=1024

   # Test data settings
   # Set to 'true' to use test data instead of connecting to SQL Server
   USE_TEST_DATA=false
   # Number of test parcel records to generate
   TEST_DATA_RECORD_COUNT=100
   ```

3. **Prepare Output Directory**

   Create an `output` directory in the same location as the executable (or specify a different directory in your `.env` file).

## Running the ETL Process

### Command Line Arguments

The executable supports several command line arguments:

- `--batch-size X`: Sets the batch size for data extraction (default: 1000)
- `--test-data`: Use test data instead of connecting to SQL Server
- `--output-dir PATH`: Specify a directory for output files
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Example Usage

1. **Run with default settings using SQL Server data**:

   ```bash
   ./CountyDataSync
   ```

2. **Run with test data**:

   ```bash
   ./CountyDataSync --test-data
   ```

3. **Run with custom batch size and output directory**:

   ```bash
   ./CountyDataSync --batch-size 500 --output-dir /path/to/outputs
   ```

## Output Files

After running the ETL process, the following files will be generated in the output directory:

1. **GeoPackage** (`geo_db.gpkg`): Contains spatial data that can be opened in GIS software
2. **Stats Database** (`stats_db.sqlite`): Contains aggregated statistics in SQLite format
3. **Working Database** (`working_db.sqlite`): Contains editable working data in SQLite format
4. **Log File** (`logs/etl_sync_YYYYMMDD_HHMMSS.log`): Contains detailed logs of the ETL process

## Troubleshooting

### Common Issues

1. **SQL Server Connection Issues**:
   - Check your SQL Server credentials in the `.env` file
   - Ensure the SQL Server is accessible from your network
   - Verify that the ODBC driver is installed on your system

2. **Missing Driver Error**:
   - For Windows: Install [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - For macOS/Linux: Follow [installation instructions for your platform](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

3. **Permission Errors**:
   - Ensure you have write permissions to the output directory
   - Check if you have sufficient database permissions

### Logging

- Check the log file in the `logs` directory for detailed information about errors
- Increase the log level to `DEBUG` for more verbose output: `--log-level DEBUG`

## Support

For additional support, contact your system administrator or the CountyDataSync development team.

## License

This software is proprietary and confidential. Unauthorized use, reproduction, or distribution is prohibited.
