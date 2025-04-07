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
    
    def __repr__(self):
        return f'<ETLJob {self.job_name}>'
    
    def duration(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None