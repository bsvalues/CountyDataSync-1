"""
Flask web application for CountyDataSync ETL process.
"""
import os
import logging
from datetime import datetime
try:
    import pandas as pd
except ImportError:
    # For development purposes, we'll handle missing pandas later
    pd = None
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

# HTML Templates
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CountyDataSync ETL{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        .navbar-brand { font-weight: bold; }
        .card { margin-bottom: 1.5rem; }
        .job-status-pending { background-color: var(--bs-warning); }
        .job-status-running { background-color: var(--bs-info); }
        .job-status-completed { background-color: var(--bs-success); }
        .job-status-failed { background-color: var(--bs-danger); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">CountyDataSync ETL</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/new-job">New ETL Job</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category if category != 'error' else 'danger' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <footer class="mt-5 py-3 bg-body-tertiary">
        <div class="container text-center">
            <p class="mb-0">CountyDataSync ETL System &copy; 2025</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
'''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CountyDataSync ETL Dashboard</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        .navbar-brand { font-weight: bold; }
        .card { margin-bottom: 1.5rem; }
        .job-status-pending { background-color: var(--bs-warning); }
        .job-status-running { background-color: var(--bs-info); }
        .job-status-completed { background-color: var(--bs-success); }
        .job-status-failed { background-color: var(--bs-danger); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">CountyDataSync ETL</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link active" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/new-job">New ETL Job</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        <h1 class="mb-4">ETL Jobs Dashboard</h1>

        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">System Information</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Total Jobs:</strong> {{ jobs|length }}</p>
                                <p><strong>Pending Jobs:</strong> {{ jobs|selectattr('status', 'equalto', 'pending')|list|length }}</p>
                                <p><strong>Running Jobs:</strong> {{ jobs|selectattr('status', 'equalto', 'running')|list|length }}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Completed Jobs:</strong> {{ jobs|selectattr('status', 'equalto', 'completed')|list|length }}</p>
                                <p><strong>Failed Jobs:</strong> {{ jobs|selectattr('status', 'equalto', 'failed')|list|length }}</p>
                                <p><strong>Last Run:</strong> {% if jobs %}{{ jobs[0].start_time.strftime('%Y-%m-%d %H:%M:%S') }}{% else %}Never{% endif %}</p>
                            </div>
                        </div>
                        <div class="mt-3">
                            <a href="/new-job" class="btn btn-primary">Create New ETL Job</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h2 class="mb-3">Recent ETL Jobs</h2>

        {% if jobs %}
            <div class="row">
                {% for job in jobs %}
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <span>{{ job.job_name }}</span>
                                <span class="badge job-status-{{ job.status }}">{{ job.status }}</span>
                            </div>
                            <div class="card-body">
                                <p><strong>Source:</strong> {{ job.source_type }}</p>
                                <p><strong>Started:</strong> {{ job.start_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                                {% if job.end_time %}
                                    <p><strong>Ended:</strong> {{ job.end_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                                    <p><strong>Duration:</strong> {{ job.duration() }} seconds</p>
                                {% endif %}
                                {% if job.record_count %}
                                    <p><strong>Records:</strong> {{ job.record_count }}</p>
                                {% endif %}
                                <div class="mt-3">
                                    <a href="/job/{{ job.id }}" class="btn btn-outline-primary">View Details</a>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="alert alert-info">
                No ETL jobs found. <a href="/new-job">Create your first ETL job</a>.
            </div>
        {% endif %}
    </div>

    <footer class="mt-5 py-3 bg-body-tertiary">
        <div class="container text-center">
            <p class="mb-0">CountyDataSync ETL System &copy; 2025</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

NEW_JOB_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New ETL Job - CountyDataSync ETL</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        .navbar-brand { font-weight: bold; }
        .card { margin-bottom: 1.5rem; }
        .job-status-pending { background-color: var(--bs-warning); }
        .job-status-running { background-color: var(--bs-info); }
        .job-status-completed { background-color: var(--bs-success); }
        .job-status-failed { background-color: var(--bs-danger); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">CountyDataSync ETL</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="/new-job">New ETL Job</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
<h1 class="mb-4">Create New ETL Job</h1>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body">
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label for="job_name" class="form-label">Job Name</label>
                        <input type="text" class="form-control" id="job_name" name="job_name" required>
                        <div class="form-text">Provide a descriptive name for this ETL job.</div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Data Source</label>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="source_type" id="source_sql" value="sql_server" checked>
                            <label class="form-check-label" for="source_sql">
                                SQL Server (Use configured connection)
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="source_type" id="source_file" value="file_upload">
                            <label class="form-check-label" for="source_file">
                                File Upload
                            </label>
                        </div>
                    </div>
                    
                    <div id="file_upload_section" class="mb-3 d-none">
                        <label for="file" class="form-label">Upload Data File</label>
                        <input type="file" class="form-control" id="file" name="file">
                        <div class="form-text">Supported file types: .csv, .xls, .xlsx</div>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">Create and Run ETL Job</button>
                        <a href="/" class="btn btn-outline-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                Tips
            </div>
            <div class="card-body">
                <h5 class="card-title">Data Source Options</h5>
                <p><strong>SQL Server:</strong> Uses the connection settings from your .env file to extract data from the MasterParcels table.</p>
                <p><strong>File Upload:</strong> Upload a CSV or Excel file containing data with a 'geometry' column in WKT format.</p>
                
                <h5 class="card-title mt-4">Expected Data Format</h5>
                <p>The data should contain a 'geometry' column with WKT (Well-Known Text) strings representing spatial geometry.</p>
                <p>Example WKT: <code>POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))</code></p>
            </div>
        </div>
    </div>
</div>
    </div>

    <footer class="mt-5 py-3 bg-body-tertiary">
        <div class="container text-center">
            <p class="mb-0">CountyDataSync ETL System &copy; 2025</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Show/hide file upload section based on source type selection
        document.addEventListener('DOMContentLoaded', function() {
            const radioButtons = document.querySelectorAll('input[name="source_type"]');
            const fileUploadSection = document.getElementById('file_upload_section');
            
            radioButtons.forEach(radio => {
                radio.addEventListener('change', function() {
                    if (this.value === 'file_upload') {
                        fileUploadSection.classList.remove('d-none');
                    } else {
                        fileUploadSection.classList.add('d-none');
                    }
                });
            });
        });
    </script>
</body>
</html>
'''

JOB_DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Details - CountyDataSync ETL</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        .navbar-brand { font-weight: bold; }
        .card { margin-bottom: 1.5rem; }
        .job-status-pending { background-color: var(--bs-warning); }
        .job-status-running { background-color: var(--bs-info); }
        .job-status-completed { background-color: var(--bs-success); }
        .job-status-failed { background-color: var(--bs-danger); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">CountyDataSync ETL</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/new-job">New ETL Job</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>ETL Job Details</h1>
    <a href="/" class="btn btn-outline-secondary">Back to Dashboard</a>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h4 class="mb-0">{{ job.job_name }}</h4>
                <span class="badge job-status-{{ job.status }}">{{ job.status }}</span>
            </div>
            <div class="card-body">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <p><strong>Job ID:</strong> {{ job.id }}</p>
                        <p><strong>Source Type:</strong> {{ job.source_type }}</p>
                        {% if job.source_file %}
                            <p><strong>Source File:</strong> {{ job.source_file.split('/')[-1] }}</p>
                        {% endif %}
                        <p><strong>Started:</strong> {{ job.start_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                    </div>
                    <div class="col-md-6">
                        {% if job.end_time %}
                            <p><strong>Ended:</strong> {{ job.end_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                            <p><strong>Duration:</strong> {{ job.duration() }} seconds</p>
                        {% endif %}
                        {% if job.record_count %}
                            <p><strong>Records Processed:</strong> {{ job.record_count }}</p>
                        {% endif %}
                    </div>
                </div>
                
                {% if job.status == 'failed' and job.error_message %}
                    <div class="alert alert-danger">
                        <h5 class="alert-heading">Error Message</h5>
                        <pre class="mb-0">{{ job.error_message }}</pre>
                    </div>
                {% endif %}
                
                {% if job.status == 'completed' %}
                    <h5 class="card-title mt-4">Output Files</h5>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>File Type</th>
                                <th>Path</th>
                                <th>Size</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if job.geo_db_path %}
                                <tr>
                                    <td>Geo DB (GeoPackage)</td>
                                    <td>{{ job.geo_db_path }}</td>
                                    <td>{{ job.geo_db_size }}</td>
                                    <td>
                                        <a href="/download/{{ job.geo_db_path }}" class="btn btn-sm btn-primary">Download</a>
                                    </td>
                                </tr>
                            {% endif %}
                            {% if job.stats_db_path %}
                                <tr>
                                    <td>Stats DB (SQLite)</td>
                                    <td>{{ job.stats_db_path }}</td>
                                    <td>{{ job.stats_db_size }}</td>
                                    <td>
                                        <a href="/download/{{ job.stats_db_path }}" class="btn btn-sm btn-primary">Download</a>
                                    </td>
                                </tr>
                            {% endif %}
                            {% if job.working_db_path %}
                                <tr>
                                    <td>Working DB (SQLite)</td>
                                    <td>{{ job.working_db_path }}</td>
                                    <td>{{ job.working_db_size }}</td>
                                    <td>
                                        <a href="/download/{{ job.working_db_path }}" class="btn btn-sm btn-primary">Download</a>
                                    </td>
                                </tr>
                            {% endif %}
                        </tbody>
                    </table>
                {% elif job.status == 'running' %}
                    <div class="alert alert-info">
                        <h5 class="alert-heading">Job In Progress</h5>
                        <p>This ETL job is currently running. Refresh the page to check for updates.</p>
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div>
                        </div>
                    </div>
                {% elif job.status == 'pending' %}
                    <div class="alert alert-warning">
                        <h5 class="alert-heading">Job Pending</h5>
                        <p>This ETL job is waiting to be started.</p>
                        <a href="/run-job/{{ job.id }}" class="btn btn-primary">Start Job Now</a>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                Job Actions
            </div>
            <div class="card-body">
                {% if job.status == 'completed' %}
                    <p>This job has completed successfully. You can download the output files or create a new job.</p>
                    <div class="d-grid gap-2">
                        <a href="/new-job" class="btn btn-primary">Create New Job</a>
                    </div>
                {% elif job.status == 'failed' %}
                    <p>This job failed to complete. You can retry or create a new job.</p>
                    <div class="d-grid gap-2">
                        <a href="/run-job/{{ job.id }}" class="btn btn-primary">Retry Job</a>
                        <a href="/new-job" class="btn btn-outline-secondary">Create New Job</a>
                    </div>
                {% elif job.status == 'pending' %}
                    <p>This job is pending execution.</p>
                    <div class="d-grid gap-2">
                        <a href="/run-job/{{ job.id }}" class="btn btn-primary">Start Job</a>
                    </div>
                {% elif job.status == 'running' %}
                    <p>This job is currently running.</p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-secondary" disabled>Job Running...</button>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

    <footer class="mt-5 py-3 bg-body-tertiary">
        <div class="container text-center">
            <p class="mb-0">CountyDataSync ETL System &copy; 2025</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Create the Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-countydatasync")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
# Get PostgreSQL database URL from environment variable
database_url = os.environ.get("DATABASE_URL")
# If using postgres:// scheme, convert to postgresql:// for SQLAlchemy
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///countydatasync.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

# Output directory
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the app with the extension
db.init_app(app)

# Import ETL modules
from etl.sync import run_etl
from etl.extract import extract_data
from etl.transform import transform_data, prepare_stats_data, prepare_working_data
from etl.load import (
    load_geo_db, 
    create_stats_db, load_stats_data,
    create_working_db, load_working_data
)
from etl.utils import get_memory_usage, format_elapsed_time, check_file_size

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the database tables
with app.app_context():
    # Import models module now that db is initialized
    from models import ETLJob
    
    # Create the database tables
    db.create_all()


# Routes
@app.route('/')
def index():
    # Get all ETL jobs
    jobs = ETLJob.query.order_by(ETLJob.start_time.desc()).all()
    
    # Get file sizes for any completed jobs
    for job in jobs:
        if job.geo_db_path and os.path.exists(job.geo_db_path):
            job.geo_db_size = check_file_size(job.geo_db_path)
        if job.stats_db_path and os.path.exists(job.stats_db_path):
            job.stats_db_size = check_file_size(job.stats_db_path)
        if job.working_db_path and os.path.exists(job.working_db_path):
            job.working_db_size = check_file_size(job.working_db_path)
    
    return render_template_string(INDEX_TEMPLATE, jobs=jobs)

@app.route('/new-job', methods=['GET', 'POST'])
def new_job():
    if request.method == 'POST':
        # Get form data
        job_name = request.form.get('job_name')
        source_type = request.form.get('source_type')
        
        if not job_name:
            flash('Job name is required.', 'error')
            return redirect(url_for('new_job'))
        
        # Create a new ETL job
        job = ETLJob(
            job_name=job_name,
            source_type=source_type
        )
        
        # Handle file upload if source type is file_upload
        if source_type == 'file_upload':
            # Check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # Update job with source file
                job.source_file = filepath
            else:
                flash('File type not allowed', 'error')
                return redirect(request.url)
        
        # Save the job to the database
        db.session.add(job)
        db.session.commit()
        
        # Start the ETL process
        return redirect(url_for('run_job', job_id=job.id))
    
    return render_template_string(NEW_JOB_TEMPLATE)

@app.route('/run-job/<int:job_id>')
def run_job(job_id):
    # Get the job
    job = ETLJob.query.get_or_404(job_id)
    
    # Update job status
    job.status = 'running'
    db.session.commit()
    
    try:
        if job.source_type == 'sql_server':
            # Run ETL from SQL Server
            logger.info(f"Starting ETL job {job.id} from SQL Server")
            
            # Run the ETL process
            output_files = run_etl()
            
            # Update job with output paths and record count
            if output_files:
                job.geo_db_path = output_files.get('geo_db')
                job.stats_db_path = output_files.get('stats_db')
                job.working_db_path = output_files.get('working_db')
                
        elif job.source_type == 'file_upload':
            # Run ETL from file upload
            logger.info(f"Starting ETL job {job.id} from file upload: {job.source_file}")
            
            # Load the file based on its extension
            file_extension = job.source_file.rsplit('.', 1)[1].lower()
            
            df = None
            if file_extension == 'csv':
                df = pd.read_csv(job.source_file)
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(job.source_file)
            
            if df is not None:
                # Record count
                job.record_count = len(df)
                
                # Transform data (adjust based on file structure)
                # Note: This assumes the file has a 'geometry' column with WKT strings
                if 'geometry' in df.columns:
                    gdf = transform_data(df)
                    
                    # Prepare data for target databases
                    stats_df = prepare_stats_data(gdf)
                    working_df = prepare_working_data(gdf)
                    
                    # Load data into target databases
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    
                    # Create unique output paths
                    geo_db_path = os.path.join(OUTPUT_DIR, f"geo_db_{timestamp}.gpkg")
                    stats_db_path = os.path.join(OUTPUT_DIR, f"stats_db_{timestamp}.sqlite")
                    working_db_path = os.path.join(OUTPUT_DIR, f"working_db_{timestamp}.sqlite")
                    
                    # Load data
                    load_geo_db(gdf, geo_db_path)
                    create_stats_db(stats_db_path)
                    load_stats_data(stats_df, stats_db_path)
                    create_working_db(working_db_path)
                    load_working_data(working_df, working_db_path)
                    
                    # Update job with output paths
                    job.geo_db_path = geo_db_path
                    job.stats_db_path = stats_db_path
                    job.working_db_path = working_db_path
                else:
                    raise ValueError("Input file does not contain a 'geometry' column with WKT strings")
            else:
                raise ValueError(f"Could not read file with extension {file_extension}")
        
        # Update job status to completed
        job.status = 'completed'
        job.end_time = datetime.utcnow()
        
    except Exception as e:
        # Handle errors
        logger.error(f"ETL job {job.id} failed: {str(e)}", exc_info=True)
        job.status = 'failed'
        job.end_time = datetime.utcnow()
        job.error_message = str(e)
    
    # Save the job
    db.session.commit()
    
    return redirect(url_for('job_detail', job_id=job.id))

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    # Get the job
    job = ETLJob.query.get_or_404(job_id)
    
    # Get file sizes
    if job.geo_db_path and os.path.exists(job.geo_db_path):
        job.geo_db_size = check_file_size(job.geo_db_path)
    if job.stats_db_path and os.path.exists(job.stats_db_path):
        job.stats_db_size = check_file_size(job.stats_db_path)
    if job.working_db_path and os.path.exists(job.working_db_path):
        job.working_db_size = check_file_size(job.working_db_path)
    
    return render_template_string(JOB_DETAIL_TEMPLATE, job=job)

@app.route('/download/<path:filename>')
def download_file(filename):
    # Extract directory from the filename
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    
    return send_from_directory(directory, file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)