"""
Flask web application for CountyDataSync ETL process.
"""
import os
import logging
import time
import json
import glob
from datetime import datetime
try:
    import pandas as pd
except ImportError:
    # For development purposes, we'll handle missing pandas later
    pd = None
from flask import Flask, render_template_string, render_template, request, redirect, url_for, flash, send_from_directory, session
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
from etl.utils import get_memory_usage, get_memory_usage_value, get_cpu_usage, format_elapsed_time, check_file_size

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
    
    return render_template('index.html', jobs=jobs)

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
    
    return render_template('new_job.html')

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
            
            # Run the ETL process with job ID for performance tracking
            output = run_etl(job_id=job.id)
            output_files = output.get('files', {})
            
            # Update job with output paths
            if output_files:
                job.geo_db_path = output_files.get('geo_db')
                job.stats_db_path = output_files.get('stats_db')
                job.working_db_path = output_files.get('working_db')
                
        elif job.source_type == 'file_upload':
            # Run ETL from file upload
            logger.info(f"Starting ETL job {job.id} from file upload: {job.source_file}")
            
            # Create a PerformanceMetric for file upload job
            from models import PerformanceMetric
            
            # Record performance metrics
            start_time = time.time()
            peak_memory = get_memory_usage_value()
            
            # Start extraction phase
            extraction_start = time.time()
            
            # Create performance metric record for extraction start
            metric = PerformanceMetric(
                job_id=job.id,
                stage='extraction',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=0,
                description="Starting file extraction"
            )
            db.session.add(metric)
            db.session.commit()
            
            # Load the file based on its extension
            file_extension = job.source_file.rsplit('.', 1)[1].lower()
            
            df = None
            if file_extension == 'csv':
                df = pd.read_csv(job.source_file)
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(job.source_file)
            
            extraction_time = time.time() - extraction_start
            current_memory = get_memory_usage_value()
            peak_memory = max(peak_memory, current_memory)
            
            if df is not None:
                # Record count
                record_count = len(df)
                job.record_count = record_count
                
                # Create performance metric record for extraction end
                metric = PerformanceMetric(
                    job_id=job.id,
                    stage='extraction',
                    memory_usage=current_memory,
                    cpu_usage=get_cpu_usage(),
                    elapsed_time=extraction_time,
                    records_processed=record_count,
                    description="File extraction completed"
                )
                db.session.add(metric)
                db.session.commit()
                
                # Start transformation phase
                transformation_start = time.time()
                
                # Create performance metric record for transformation start
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
                
                # Transform data (adjust based on file structure)
                # Note: This assumes the file has a 'geometry' column with WKT strings
                if 'geometry' in df.columns:
                    gdf = transform_data(df)
                    
                    transformation_time = time.time() - transformation_start
                    current_memory = get_memory_usage_value()
                    peak_memory = max(peak_memory, current_memory)
                    
                    # Create performance metric record for transformation end
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
                    
                    # Prepare data for target databases
                    stats_df = prepare_stats_data(gdf)
                    working_df = prepare_working_data(gdf)
                    
                    # Start loading phase
                    loading_start = time.time()
                    
                    # Create performance metric record for loading start
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
                    
                    # Create unique output paths
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    geo_db_path = os.path.join(OUTPUT_DIR, f"geo_db_{timestamp}.gpkg")
                    stats_db_path = os.path.join(OUTPUT_DIR, f"stats_db_{timestamp}.sqlite")
                    working_db_path = os.path.join(OUTPUT_DIR, f"working_db_{timestamp}.sqlite")
                    
                    # Load data
                    load_geo_db(gdf, geo_db_path)
                    create_stats_db(stats_db_path)
                    load_stats_data(stats_df, stats_db_path)
                    create_working_db(working_db_path)
                    load_working_data(working_df, working_db_path)
                    
                    loading_time = time.time() - loading_start
                    current_memory = get_memory_usage_value()
                    peak_memory = max(peak_memory, current_memory)
                    
                    # Create performance metric record for loading end
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
                    
                    # Update job with output paths and performance metrics
                    job.geo_db_path = geo_db_path
                    job.stats_db_path = stats_db_path
                    job.working_db_path = working_db_path
                    job.extraction_time = extraction_time
                    job.transformation_time = transformation_time
                    job.loading_time = loading_time
                    job.peak_memory_usage = peak_memory
                else:
                    raise ValueError("Input file does not contain a 'geometry' column with WKT strings")
            else:
                raise ValueError(f"Could not read file with extension {file_extension}")
        
        # Update job status to completed
        job.status = 'completed'
        job.end_time = datetime.utcnow()
        
        # Run data quality analysis if job completed successfully
        try:
            from etl.integrate_quality_heatmap import analyze_etl_output
            
            # Create a performance metric for data quality analysis
            quality_start = time.time()
            metric = PerformanceMetric(
                job_id=job.id,
                stage='data_quality',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=time.time() - start_time,
                description="Starting data quality analysis"
            )
            db.session.add(metric)
            db.session.commit()
            
            # Run the analysis
            report_paths = analyze_etl_output(job)
            
            # Record completion metric
            quality_time = time.time() - quality_start
            metric = PerformanceMetric(
                job_id=job.id,
                stage='data_quality',
                memory_usage=get_memory_usage_value(),
                cpu_usage=get_cpu_usage(),
                elapsed_time=quality_time,
                description="Data quality analysis completed"
            )
            db.session.add(metric)
            db.session.commit()
            
            # Log the results
            if report_paths:
                logger.info(f"Data quality analysis completed for job {job.id}. Reports: {report_paths}")
            else:
                logger.warning(f"Data quality analysis produced no reports for job {job.id}")
        
        except Exception as quality_error:
            # Don't fail the job if quality analysis fails
            logger.error(f"Data quality analysis failed for job {job.id}: {str(quality_error)}", exc_info=True)
        
    except Exception as e:
        # Handle errors in the main ETL process
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
    
    # Get performance metrics
    from models import PerformanceMetric
    metrics = PerformanceMetric.query.filter_by(job_id=job.id).order_by(PerformanceMetric.timestamp).all()
    
    # Get file sizes
    if job.geo_db_path and os.path.exists(job.geo_db_path):
        job.geo_db_size = check_file_size(job.geo_db_path)
    if job.stats_db_path and os.path.exists(job.stats_db_path):
        job.stats_db_size = check_file_size(job.stats_db_path)
    if job.working_db_path and os.path.exists(job.working_db_path):
        job.working_db_size = check_file_size(job.working_db_path)
    
    # Check if a data quality heatmap exists for this job
    has_quality_report = False
    if job.stats_db_path:
        job_output_dir = os.path.join('output', f"job_{job.id}")
        if os.path.exists(job_output_dir) and len(os.listdir(job_output_dir)) > 0:
            has_quality_report = True
    
    return render_template('job_detail.html', job=job, metrics=metrics, has_quality_report=has_quality_report)

@app.route('/data-quality-heatmap')
def data_quality_heatmap():
    """
    Display the interactive data quality heatmap.
    """
    # Get job_id from query parameter, default to the latest completed job
    job_id = request.args.get('job_id', None)
    
    if job_id:
        job = ETLJob.query.get(job_id)
    else:
        # Get the latest completed job
        job = ETLJob.query.filter_by(status='completed').order_by(ETLJob.end_time.desc()).first()
    
    if not job:
        # No completed jobs found
        return render_template(
            'data_quality_heatmap.html',
            heatmap_data=None
        )
    
    # Get previous and next job IDs for navigation
    previous_job = ETLJob.query.filter(
        ETLJob.status == 'completed',
        ETLJob.id < job.id
    ).order_by(ETLJob.id.desc()).first()
    
    next_job = ETLJob.query.filter(
        ETLJob.status == 'completed',
        ETLJob.id > job.id
    ).order_by(ETLJob.id.asc()).first()
    
    # Check if a heatmap data file exists for this job
    heatmap_file = None
    if job.stats_db_path:
        # Look for a heatmap file in the same directory
        stats_dir = os.path.dirname(job.stats_db_path)
        heatmap_files = glob.glob(os.path.join(stats_dir, 'parcel_data_quality_heatmap_*.json'))
        if heatmap_files:
            # Use the latest heatmap file
            heatmap_file = sorted(heatmap_files)[-1]
    
    heatmap_data = None
    column_details = {}
    
    if heatmap_file and os.path.exists(heatmap_file):
        try:
            with open(heatmap_file, 'r') as f:
                heatmap_data = json.load(f)
            
            # Extract column details from the full quality report
            quality_report_file = heatmap_file.replace('_heatmap_', '_')
            if os.path.exists(quality_report_file):
                with open(quality_report_file, 'r') as f:
                    quality_report = json.load(f)
                    column_details = quality_report.get('columns', {})
        except Exception as e:
            app.logger.error(f"Error loading heatmap data: {str(e)}")
    
    # If we still don't have heatmap data, generate mock data for the UI
    # This would be replaced with real data in production
    if not heatmap_data:
        # Get column names from a sample file or database
        columns = []
        data = []
        metrics = ['completeness', 'validity', 'consistency', 'outliers', 'overall_score']
    else:
        columns = heatmap_data.get('columns', [])
        metrics = heatmap_data.get('metrics', [])
        data = heatmap_data.get('data', [])
    
    # Get completion metrics
    complete_records = 0
    complete_records_percentage = 0
    record_count = job.record_count or 0
    analysis_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Helper function for Jinja to compute colors
    def get_color(value):
        """Generate a color from red (0%) to blue (100%)"""
        # Ensure value is between 0 and 100
        value = max(0, min(100, value))
        
        if value < 25:
            # Red to orange (0-25%)
            r = 178
            g = 24 + (value / 25) * (96 - 24)
            b = 43
        elif value < 50:
            # Orange to yellow (25-50%)
            r = 178 + (value - 25) / 25 * (244 - 178)
            g = 96 + (value - 25) / 25 * (165 - 96)
            b = 43 + (value - 25) / 25 * (130 - 43)
        elif value < 75:
            # Yellow to light blue (50-75%)
            r = 244 - (value - 50) / 25 * (244 - 146)
            g = 165 + (value - 50) / 25 * (197 - 165)
            b = 130 + (value - 50) / 25 * (222 - 130)
        else:
            # Light blue to dark blue (75-100%)
            r = 146 - (value - 75) / 25 * (146 - 33)
            g = 197 - (value - 75) / 25 * (197 - 102)
            b = 222 - (value - 75) / 25 * (222 - 172)
            
        return f'rgb({int(r)}, {int(g)}, {int(b)})'
    
    return render_template(
        'data_quality_heatmap.html',
        job_id=job.id if job else None,
        job_name=job.job_name if job else None,
        record_count=record_count,
        complete_records=complete_records,
        complete_records_percentage=complete_records_percentage,
        analysis_timestamp=analysis_timestamp,
        heatmap_data=heatmap_data is not None,
        columns=columns,
        metrics=metrics,
        data=data,
        column_details=column_details,
        get_color=get_color,
        has_previous_job=previous_job is not None,
        has_next_job=next_job is not None,
        previous_job_id=previous_job.id if previous_job else None,
        next_job_id=next_job.id if next_job else None
    )

@app.route('/performance-dashboard')
def performance_dashboard():
    # Get all completed jobs
    jobs = ETLJob.query.filter_by(status='completed').order_by(ETLJob.end_time.desc()).all()
    
    # Calculate averages for completed jobs with performance metrics
    valid_jobs = [job for job in jobs if job.extraction_time and job.transformation_time and job.loading_time and job.record_count]
    
    if valid_jobs:
        avg_extraction_time = sum(job.extraction_time for job in valid_jobs) / len(valid_jobs)
        avg_transformation_time = sum(job.transformation_time for job in valid_jobs) / len(valid_jobs)
        avg_loading_time = sum(job.loading_time for job in valid_jobs) / len(valid_jobs)
        avg_duration = sum(job.duration() for job in valid_jobs) / len(valid_jobs)
        avg_records = sum(job.record_count for job in valid_jobs) / len(valid_jobs)
        avg_memory = sum(job.peak_memory_usage for job in valid_jobs if job.peak_memory_usage) / len(valid_jobs) if any(job.peak_memory_usage for job in valid_jobs) else 0
        
        # Calculate derived metrics
        avg_throughput = sum(job.throughput() for job in valid_jobs if job.throughput()) / len(valid_jobs) if any(job.throughput() for job in valid_jobs) else 0
        avg_memory_per_record = sum(job.peak_memory_usage / job.record_count for job in valid_jobs if job.peak_memory_usage and job.record_count) / len(valid_jobs) if any(job.peak_memory_usage and job.record_count for job in valid_jobs) else 0
    else:
        avg_extraction_time = 0
        avg_transformation_time = 0
        avg_loading_time = 0
        avg_duration = 0
        avg_records = 0
        avg_memory = 0
        avg_throughput = 0
        avg_memory_per_record = 0
    
    # Calculate percentages for ETL stages
    total_time = avg_extraction_time + avg_transformation_time + avg_loading_time
    if total_time > 0:
        avg_extraction_pct = (avg_extraction_time / total_time) * 100
        avg_transformation_pct = (avg_transformation_time / total_time) * 100
        avg_loading_pct = (avg_loading_time / total_time) * 100
    else:
        avg_extraction_pct = avg_transformation_pct = avg_loading_pct = 0
        
    # Get all jobs for stats
    all_jobs = ETLJob.query.order_by(ETLJob.start_time.desc()).all()
    total_jobs = len(all_jobs)
    
    return render_template('performance_dashboard.html', 
                           jobs=valid_jobs,
                           all_jobs=all_jobs,
                           total_jobs=total_jobs,
                           avg_extraction_time=avg_extraction_time,
                           avg_transformation_time=avg_transformation_time,
                           avg_loading_time=avg_loading_time,
                           avg_extraction_pct=avg_extraction_pct,
                           avg_transformation_pct=avg_transformation_pct,
                           avg_loading_pct=avg_loading_pct,
                           avg_duration=avg_duration,
                           avg_records=avg_records,
                           avg_memory=avg_memory,
                           avg_throughput=avg_throughput,
                           avg_memory_per_record=avg_memory_per_record)

@app.route('/download/<path:filename>')
def download_file(filename):
    # Extract directory from the filename
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    
    return send_from_directory(directory, file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)