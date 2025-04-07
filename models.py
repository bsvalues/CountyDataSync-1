"""
Database models for CountyDataSync ETL process.
"""
from datetime import datetime
from app import db

class ETLJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    source_type = db.Column(db.String(20), nullable=False)  # sql_server, file_upload
    source_file = db.Column(db.String(255), nullable=True)
    geo_db_path = db.Column(db.String(255), nullable=True)
    stats_db_path = db.Column(db.String(255), nullable=True)
    working_db_path = db.Column(db.String(255), nullable=True)
    record_count = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Performance metrics
    extraction_time = db.Column(db.Float, nullable=True)  # Time in seconds
    transformation_time = db.Column(db.Float, nullable=True)  # Time in seconds
    loading_time = db.Column(db.Float, nullable=True)  # Time in seconds
    peak_memory_usage = db.Column(db.Float, nullable=True)  # Memory in MB
    
    # Relationships
    performance_metrics = db.relationship('PerformanceMetric', back_populates='job', lazy='dynamic')
    
    def __repr__(self):
        return f'<ETLJob {self.job_name}>'
    
    def duration(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def throughput(self):
        """Calculate records processed per second"""
        if self.record_count and self.duration():
            return self.record_count / self.duration()
        return None
    
    def extraction_percentage(self):
        """Calculate extraction time as percentage of total duration"""
        if self.extraction_time and self.duration():
            return (self.extraction_time / self.duration()) * 100
        return None
    
    def transformation_percentage(self):
        """Calculate transformation time as percentage of total duration"""
        if self.transformation_time and self.duration():
            return (self.transformation_time / self.duration()) * 100
        return None
    
    def loading_percentage(self):
        """Calculate loading time as percentage of total duration"""
        if self.loading_time and self.duration():
            return (self.loading_time / self.duration()) * 100
        return None

class PerformanceMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('etl_job.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stage = db.Column(db.String(50), nullable=False)  # extraction, transformation, loading
    memory_usage = db.Column(db.Float, nullable=True)  # Memory in MB
    cpu_usage = db.Column(db.Float, nullable=True)  # CPU usage in percentage
    elapsed_time = db.Column(db.Float, nullable=True)  # Time in seconds since job start
    records_processed = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    
    # Relationship
    job = db.relationship('ETLJob', back_populates='performance_metrics')
    
    def __repr__(self):
        return f'<PerformanceMetric {self.stage} at {self.timestamp}>'