"""
Data quality analysis and visualization module for CountyDataSync ETL process.
Provides functionality for generating data quality metrics and heatmaps.
"""
import os
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime
from etl.utils import ensure_directory_exists, get_timestamp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/data_quality.log'
)
logger = logging.getLogger(__name__)

class DataQualityAnalyzer:
    """
    Class for analyzing data quality and generating metrics for visualization.
    """
    def __init__(self, output_dir='output'):
        """
        Initialize DataQualityAnalyzer instance.
        
        Args:
            output_dir (str): Directory to save output files
        """
        self.output_dir = output_dir
        ensure_directory_exists(output_dir)
        
    def analyze_column_quality(self, df, column_name):
        """
        Analyze the quality of a specific column in the DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            column_name (str): Name of the column to analyze
            
        Returns:
            dict: Quality metrics for the column
        """
        # Basic metrics
        metrics = {
            'column_name': column_name,
            'null_count': df[column_name].isnull().sum(),
            'null_percentage': (df[column_name].isnull().sum() / len(df)) * 100,
        }
        
        # Column type-specific metrics
        if df[column_name].dtype == 'object':
            # String-based analysis
            metrics.update({
                'unique_values': df[column_name].nunique(),
                'unique_percentage': (df[column_name].nunique() / len(df)) * 100,
                'max_length': df[column_name].astype(str).str.len().max(),
                'min_length': df[column_name].astype(str).str.len().min(),
                'empty_strings': (df[column_name] == '').sum(),
                'empty_strings_percentage': ((df[column_name] == '').sum() / len(df)) * 100
            })
            
            # Most common values
            value_counts = df[column_name].value_counts().head(5).to_dict()
            metrics['most_common_values'] = value_counts
            
        elif np.issubdtype(df[column_name].dtype, np.number):
            # Numeric analysis
            metrics.update({
                'min': df[column_name].min(),
                'max': df[column_name].max(),
                'mean': df[column_name].mean(),
                'median': df[column_name].median(),
                'std': df[column_name].std(),
                'zeros': (df[column_name] == 0).sum(),
                'zeros_percentage': ((df[column_name] == 0).sum() / len(df)) * 100,
                'negative_values': (df[column_name] < 0).sum(),
                'negative_percentage': ((df[column_name] < 0).sum() / len(df)) * 100,
            })
            
            # Outlier detection (values outside 3 standard deviations)
            if not pd.isna(metrics['std']) and metrics['std'] != 0:
                mean = metrics['mean']
                std = metrics['std']
                outliers = df[(df[column_name] < mean - 3 * std) | (df[column_name] > mean + 3 * std)][column_name]
                metrics['outliers_count'] = len(outliers)
                metrics['outliers_percentage'] = (len(outliers) / len(df)) * 100
            else:
                metrics['outliers_count'] = 0
                metrics['outliers_percentage'] = 0
                
        elif pd.api.types.is_datetime64_dtype(df[column_name]):
            # Date/time analysis
            metrics.update({
                'min_date': df[column_name].min().isoformat(),
                'max_date': df[column_name].max().isoformat(),
                'range_days': (df[column_name].max() - df[column_name].min()).days,
                'future_dates': (df[column_name] > pd.Timestamp.now()).sum(),
                'future_dates_percentage': ((df[column_name] > pd.Timestamp.now()).sum() / len(df)) * 100
            })
            
        return metrics
    
    def analyze_dataframe_quality(self, df):
        """
        Analyze the quality of all columns in the DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            dict: Quality metrics for the entire DataFrame
        """
        # Overall metrics
        overall_metrics = {
            'record_count': len(df),
            'column_count': len(df.columns),
            'timestamp': datetime.now().isoformat(),
            'complete_records': (df.notnull().all(axis=1)).sum(),
            'complete_records_percentage': ((df.notnull().all(axis=1)).sum() / len(df)) * 100,
        }
        
        # Column-specific metrics
        column_metrics = {}
        for column in df.columns:
            try:
                column_metrics[column] = self.analyze_column_quality(df, column)
            except Exception as e:
                logger.error(f"Error analyzing column {column}: {str(e)}")
                column_metrics[column] = {
                    'column_name': column,
                    'error': str(e)
                }
        
        # Calculate heatmap data
        heatmap_data = self.calculate_heatmap_data(df, column_metrics)
        
        return {
            'overall': overall_metrics,
            'columns': column_metrics,
            'heatmap': heatmap_data
        }
    
    def calculate_heatmap_data(self, df, column_metrics):
        """
        Calculate data for the quality heatmap visualization.
        
        Args:
            df (pd.DataFrame): DataFrame being analyzed
            column_metrics (dict): Metrics for individual columns
            
        Returns:
            dict: Heatmap-ready data structure
        """
        heatmap_data = {
            'columns': [],
            'metrics': [
                'completeness',
                'validity',
                'consistency',
                'outliers',
                'overall_score'
            ],
            'data': []
        }
        
        # Process each column
        for column, metrics in column_metrics.items():
            heatmap_data['columns'].append(column)
            
            # Skip columns with errors
            if 'error' in metrics:
                heatmap_data['data'].append([0, 0, 0, 0, 0])
                continue
                
            # Calculate quality scores (0-100)
            try:
                # Completeness: 100 - null_percentage
                completeness = 100 - metrics.get('null_percentage', 0)
                
                # Validity score based on column type
                validity = 100
                if 'empty_strings_percentage' in metrics:
                    validity -= metrics['empty_strings_percentage']
                if 'negative_percentage' in metrics and metrics.get('negative_percentage', 0) > 0:
                    # Adjust if negative values are not valid for this column (domain-specific)
                    validity -= metrics['negative_percentage']
                
                # Consistency score
                consistency = 100
                if 'unique_percentage' in metrics:
                    # For categorical columns, high uniqueness might indicate inconsistency
                    if metrics['unique_percentage'] > 95 and len(df) > 100:
                        consistency = 100 - (metrics['unique_percentage'] - 95) * 20
                
                # Outliers score: 100 - outliers_percentage
                outliers = 100
                if 'outliers_percentage' in metrics:
                    outliers = 100 - metrics.get('outliers_percentage', 0)
                
                # Overall score: average of other scores
                overall_score = (completeness + validity + consistency + outliers) / 4
                
                # Ensure scores are between 0 and 100
                completeness = max(0, min(100, completeness))
                validity = max(0, min(100, validity))
                consistency = max(0, min(100, consistency))
                outliers = max(0, min(100, outliers))
                overall_score = max(0, min(100, overall_score))
                
                heatmap_data['data'].append([
                    completeness,
                    validity,
                    consistency,
                    outliers,
                    overall_score
                ])
            except Exception as e:
                logger.error(f"Error calculating heatmap data for column {column}: {str(e)}")
                heatmap_data['data'].append([0, 0, 0, 0, 0])
        
        return heatmap_data
    
    def generate_quality_report(self, df, report_name='data_quality_report'):
        """
        Generate a comprehensive data quality report.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            report_name (str): Base name for the report files
            
        Returns:
            dict: Paths to the generated report files
        """
        # Analyze data quality
        quality_metrics = self.analyze_dataframe_quality(df)
        
        # Generate timestamp for file names
        timestamp = get_timestamp()
        
        # Save JSON report
        json_path = os.path.join(self.output_dir, f"{report_name}_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump(quality_metrics, f, indent=2)
        
        # Save CSV summary report
        csv_path = os.path.join(self.output_dir, f"{report_name}_summary_{timestamp}.csv")
        summary_data = []
        for column, metrics in quality_metrics['columns'].items():
            if 'error' in metrics:
                continue
                
            row = {
                'column_name': column,
                'null_percentage': metrics.get('null_percentage', 0),
                'completeness': 100 - metrics.get('null_percentage', 0)
            }
            
            if 'empty_strings_percentage' in metrics:
                row['empty_strings_percentage'] = metrics['empty_strings_percentage']
            
            if 'outliers_percentage' in metrics:
                row['outliers_percentage'] = metrics['outliers_percentage']
                
            if 'unique_percentage' in metrics:
                row['unique_percentage'] = metrics['unique_percentage']
                
            summary_data.append(row)
            
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(csv_path, index=False)
        
        # Save heatmap data in a separate JSON file for the visualization
        heatmap_path = os.path.join(self.output_dir, f"{report_name}_heatmap_{timestamp}.json")
        with open(heatmap_path, 'w') as f:
            json.dump(quality_metrics['heatmap'], f, indent=2)
        
        return {
            'json_report': json_path,
            'csv_summary': csv_path,
            'heatmap_data': heatmap_path,
            'timestamp': timestamp
        }

def analyze_parcel_data(df, output_dir='output'):
    """
    Convenience function to analyze parcel data quality.
    
    Args:
        df (pd.DataFrame): DataFrame with parcel data
        output_dir (str): Directory to save output files
        
    Returns:
        dict: Paths to the generated report files
    """
    analyzer = DataQualityAnalyzer(output_dir=output_dir)
    return analyzer.generate_quality_report(df, report_name='parcel_data_quality')