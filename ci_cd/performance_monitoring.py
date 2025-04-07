"""
Performance monitoring script for CI/CD pipelines.
Analyzes ETL job performance and reports trends over time.
"""
import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Ensure output directories exist
os.makedirs('ci_cd/reports', exist_ok=True)
os.makedirs('ci_cd/artifacts', exist_ok=True)

def extract_performance_data_from_db(db_url=None):
    """
    Extract performance data from the application database.
    Falls back to local SQLite if DATABASE_URL is not provided.
    
    Args:
        db_url (str, optional): Database connection URL
        
    Returns:
        pd.DataFrame: Performance metrics from the database
    """
    # Use SQLite for local development/testing if no DATABASE_URL
    if not db_url:
        # Check if a local testing database exists, if not, return empty dataframe
        if not os.path.exists('instance/test.db'):
            return pd.DataFrame()
        
        conn = sqlite3.connect('instance/test.db')
        # Query ETL job data
        try:
            # Try to get performance data from database
            df_jobs = pd.read_sql(
                """
                SELECT id, job_name, start_time, end_time, status, 
                       record_count, extraction_time, transformation_time,
                       loading_time, peak_memory_usage
                FROM etl_job
                WHERE end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT 100
                """, 
                conn
            )
            
            # Get performance metrics for each job
            df_metrics = pd.read_sql(
                """
                SELECT job_id, stage, memory_usage, cpu_usage, elapsed_time,
                       records_processed, timestamp
                FROM performance_metric
                WHERE job_id IN (SELECT id FROM etl_job WHERE end_time IS NOT NULL)
                ORDER BY timestamp DESC
                LIMIT 1000
                """,
                conn
            )
            
            return {
                'jobs': df_jobs,
                'metrics': df_metrics
            }
        except:
            # Tables might not exist yet
            return {
                'jobs': pd.DataFrame(),
                'metrics': pd.DataFrame()
            }
    else:
        # Use PostgreSQL connection if available
        try:
            import psycopg2
            from sqlalchemy import create_engine
            
            engine = create_engine(db_url)
            
            # Query ETL job data
            df_jobs = pd.read_sql(
                """
                SELECT id, job_name, start_time, end_time, status, 
                       record_count, extraction_time, transformation_time,
                       loading_time, peak_memory_usage
                FROM etl_job
                WHERE end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT 100
                """, 
                engine
            )
            
            # Get performance metrics for each job
            df_metrics = pd.read_sql(
                """
                SELECT job_id, stage, memory_usage, cpu_usage, elapsed_time,
                       records_processed, timestamp
                FROM performance_metric
                WHERE job_id IN (SELECT id FROM etl_job WHERE end_time IS NOT NULL)
                ORDER BY timestamp DESC
                LIMIT 1000
                """,
                engine
            )
            
            return {
                'jobs': df_jobs,
                'metrics': df_metrics
            }
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            return {
                'jobs': pd.DataFrame(),
                'metrics': pd.DataFrame()
            }

def generate_performance_report(data, output_dir='ci_cd/reports'):
    """
    Generate a performance report for CI/CD pipelines.
    
    Args:
        data (dict): Dictionary with jobs and metrics DataFrames
        output_dir (str): Directory to save reports
        
    Returns:
        dict: Report summary data
    """
    if data['jobs'].empty:
        print("No job data available for reporting")
        return {
            'status': 'no_data',
            'message': 'No job data available for reporting'
        }
    
    # Calculate key metrics
    summary = {
        'total_jobs': len(data['jobs']),
        'successful_jobs': len(data['jobs'][data['jobs']['status'] == 'completed']),
        'failed_jobs': len(data['jobs'][data['jobs']['status'] == 'failed']),
        'avg_duration': None,
        'avg_memory_usage': None,
        'avg_extraction_time': None,
        'avg_transformation_time': None,
        'avg_loading_time': None,
        'record_count_trend': [],
        'performance_trend': [],
        'timestamp': datetime.now().isoformat()
    }
    
    # Calculate average durations for completed jobs
    completed_jobs = data['jobs'][data['jobs']['status'] == 'completed']
    if not completed_jobs.empty:
        # Convert time columns to datetime if they're strings
        if completed_jobs['start_time'].dtype == 'object':
            completed_jobs['start_time'] = pd.to_datetime(completed_jobs['start_time'])
        if completed_jobs['end_time'].dtype == 'object':
            completed_jobs['end_time'] = pd.to_datetime(completed_jobs['end_time'])
        
        # Calculate duration in seconds
        completed_jobs['duration'] = (completed_jobs['end_time'] - 
                                     completed_jobs['start_time']).dt.total_seconds()
        
        summary['avg_duration'] = completed_jobs['duration'].mean()
        summary['avg_memory_usage'] = completed_jobs['peak_memory_usage'].mean()
        summary['avg_extraction_time'] = completed_jobs['extraction_time'].mean()
        summary['avg_transformation_time'] = completed_jobs['transformation_time'].mean()
        summary['avg_loading_time'] = completed_jobs['loading_time'].mean()
        
        # Create time series data for trends (last 10 jobs)
        last_jobs = completed_jobs.sort_values('start_time').tail(10)
        for _, job in last_jobs.iterrows():
            summary['record_count_trend'].append({
                'job_id': int(job['id']),
                'timestamp': job['start_time'].isoformat(),
                'record_count': int(job['record_count']) if pd.notna(job['record_count']) else 0,
                'duration': float(job['duration']) if pd.notna(job['duration']) else 0
            })
            
            summary['performance_trend'].append({
                'job_id': int(job['id']),
                'extraction_time': float(job['extraction_time']) if pd.notna(job['extraction_time']) else 0,
                'transformation_time': float(job['transformation_time']) if pd.notna(job['transformation_time']) else 0,
                'loading_time': float(job['loading_time']) if pd.notna(job['loading_time']) else 0,
                'memory_usage': float(job['peak_memory_usage']) if pd.notna(job['peak_memory_usage']) else 0
            })
    
    # Generate visualizations
    if not completed_jobs.empty and len(completed_jobs) > 1:
        # Plot ETL phase times
        plot_job_phase_times(completed_jobs, output_dir)
        
        # Plot memory usage trends
        if 'peak_memory_usage' in completed_jobs.columns:
            plot_memory_usage_trend(completed_jobs, output_dir)
        
        # Plot record throughput
        if 'record_count' in completed_jobs.columns:
            plot_record_throughput(completed_jobs, output_dir)
    
    # Save summary report
    summary_file = os.path.join(output_dir, 'performance_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def plot_job_phase_times(df, output_dir):
    """
    Plot ETL phase times for completed jobs.
    
    Args:
        df (pd.DataFrame): DataFrame with job data
        output_dir (str): Directory to save plots
    """
    plt.figure(figsize=(10, 6))
    
    # Get last 10 jobs for better visualization
    df = df.sort_values('start_time').tail(10)
    
    # Create DataFrame for plotting
    plot_data = pd.DataFrame({
        'Job ID': df['id'],
        'Extraction': df['extraction_time'],
        'Transformation': df['transformation_time'],
        'Loading': df['loading_time']
    }).set_index('Job ID')
    
    # Plot stacked bar chart
    plot_data.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.title('ETL Phase Times by Job')
    plt.ylabel('Time (seconds)')
    plt.xlabel('Job ID')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'etl_phase_times.png'))
    plt.close()

def plot_memory_usage_trend(df, output_dir):
    """
    Plot memory usage trend for completed jobs.
    
    Args:
        df (pd.DataFrame): DataFrame with job data
        output_dir (str): Directory to save plots
    """
    plt.figure(figsize=(10, 6))
    
    # Sort by start time
    df = df.sort_values('start_time')
    
    # Create plot
    plt.plot(df['start_time'], df['peak_memory_usage'], marker='o')
    plt.title('Peak Memory Usage Trend')
    plt.ylabel('Memory Usage (MB)')
    plt.xlabel('Job Start Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'memory_usage_trend.png'))
    plt.close()

def plot_record_throughput(df, output_dir):
    """
    Plot record throughput for completed jobs.
    
    Args:
        df (pd.DataFrame): DataFrame with job data
        output_dir (str): Directory to save plots
    """
    plt.figure(figsize=(10, 6))
    
    # Calculate throughput (records per second)
    df = df.copy()
    if 'duration' not in df.columns:
        df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds()
    
    df['throughput'] = df['record_count'] / df['duration']
    
    # Sort by start time
    df = df.sort_values('start_time')
    
    # Create plot
    plt.plot(df['start_time'], df['throughput'], marker='o')
    plt.title('Record Throughput Trend')
    plt.ylabel('Records per Second')
    plt.xlabel('Job Start Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'record_throughput.png'))
    plt.close()

def check_performance_regression(current_data, threshold=0.2):
    """
    Check for performance regression compared to previous runs.
    
    Args:
        current_data (dict): Current performance data
        threshold (float): Regression threshold (0.2 = 20% worse)
        
    Returns:
        dict: Regression analysis results
    """
    # Load previous summary if exists
    summary_file = 'ci_cd/reports/performance_summary.json'
    if not os.path.exists(summary_file):
        return {
            'status': 'baseline',
            'message': 'No previous data for comparison'
        }
    
    try:
        with open(summary_file, 'r') as f:
            previous_data = json.load(f)
        
        # Check for regressions
        regressions = []
        
        # Check average duration
        if (current_data['avg_duration'] and previous_data['avg_duration'] and
            current_data['avg_duration'] > previous_data['avg_duration'] * (1 + threshold)):
            regressions.append({
                'metric': 'avg_duration',
                'previous': previous_data['avg_duration'],
                'current': current_data['avg_duration'],
                'change_pct': ((current_data['avg_duration'] - previous_data['avg_duration']) / 
                              previous_data['avg_duration']) * 100
            })
        
        # Check average memory usage
        if (current_data['avg_memory_usage'] and previous_data['avg_memory_usage'] and
            current_data['avg_memory_usage'] > previous_data['avg_memory_usage'] * (1 + threshold)):
            regressions.append({
                'metric': 'avg_memory_usage',
                'previous': previous_data['avg_memory_usage'],
                'current': current_data['avg_memory_usage'],
                'change_pct': ((current_data['avg_memory_usage'] - previous_data['avg_memory_usage']) / 
                              previous_data['avg_memory_usage']) * 100
            })
        
        # Check ETL phase times
        for phase in ['avg_extraction_time', 'avg_transformation_time', 'avg_loading_time']:
            if (current_data[phase] and previous_data[phase] and
                current_data[phase] > previous_data[phase] * (1 + threshold)):
                regressions.append({
                    'metric': phase,
                    'previous': previous_data[phase],
                    'current': current_data[phase],
                    'change_pct': ((current_data[phase] - previous_data[phase]) / 
                                  previous_data[phase]) * 100
                })
        
        if regressions:
            return {
                'status': 'regression',
                'regressions': regressions,
                'message': f'Detected {len(regressions)} performance regressions'
            }
        else:
            return {
                'status': 'pass',
                'message': 'No performance regressions detected'
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking for performance regression: {str(e)}'
        }

def main():
    """
    Main function for the performance monitoring script.
    """
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    
    # Extract performance data
    data = extract_performance_data_from_db(db_url)
    
    # Generate performance report
    report = generate_performance_report(data)
    
    # Check for performance regression
    regression_check = check_performance_regression(report)
    
    # Print summary
    print("\n=== ETL Performance Report ===")
    print(f"Total jobs analyzed: {report.get('total_jobs', 0)}")
    print(f"Successful jobs: {report.get('successful_jobs', 0)}")
    print(f"Failed jobs: {report.get('failed_jobs', 0)}")
    
    if report.get('avg_duration'):
        print(f"\nAverage job duration: {report['avg_duration']:.2f} seconds")
        print(f"Average memory usage: {report['avg_memory_usage']:.2f} MB")
        print(f"Average extraction time: {report['avg_extraction_time']:.2f} seconds")
        print(f"Average transformation time: {report['avg_transformation_time']:.2f} seconds")
        print(f"Average loading time: {report['avg_loading_time']:.2f} seconds")
    
    print(f"\nRegression check status: {regression_check['status']}")
    print(f"Message: {regression_check['message']}")
    
    if regression_check['status'] == 'regression':
        print("\nPerformance regressions detected:")
        for reg in regression_check['regressions']:
            print(f"  - {reg['metric']}: {reg['previous']:.2f} -> {reg['current']:.2f} ({reg['change_pct']:.2f}% worse)")
    
    # Return non-zero exit code if regression detected (for CI/CD)
    if regression_check['status'] == 'regression':
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()