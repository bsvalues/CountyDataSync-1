"""
Main entry point for CountyDataSync ETL process.
"""
import os
import logging
from app import app
from models import ETLJob

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_process.log')
    ]
)

logger = logging.getLogger(__name__)

# Ensure required directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Enable test data mode by default if running locally
if os.environ.get('USE_TEST_DATA') is None:
    os.environ['USE_TEST_DATA'] = 'true'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
