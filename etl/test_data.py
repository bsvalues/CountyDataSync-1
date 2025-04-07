"""
Test data generator for CountyDataSync ETL process.
Provides functionality to generate test data for development and testing purposes.
"""
import os
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.wkt import dumps as wkt_dumps

def generate_test_parcel_data(count=100, random_seed=42):
    """
    Generate synthetic parcel data for testing.
    
    Args:
        count (int): Number of parcels to generate
        random_seed (int): Random seed for reproducibility
        
    Returns:
        pd.DataFrame: DataFrame containing parcel data with geometry in WKT format
    """
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Generate base coordinates (roughly in a state-sized area)
    base_lat = 37.0
    base_lon = -122.0
    
    # Create empty DataFrame
    data = {
        'ParcelID': range(1, count + 1),
        'Address': [],
        'City': [],
        'State': 'CA',
        'ZipCode': [],
        'LandUse': [],
        'ZoningCode': [],
        'Acres': [],
        'AssessedValue': [],
        'SaleDate': [],
        'SalePrice': [],
        'YearBuilt': [],
        'SquareFeet': [],
        'Bedrooms': [],
        'Bathrooms': [],
        'geometry': []
    }
    
    # Land use codes
    land_uses = ['Residential', 'Commercial', 'Industrial', 'Agricultural', 'Vacant']
    # City names
    cities = ['Springfield', 'Riverdale', 'Oak Valley', 'Pine Hill', 'Cedar Creek']
    # Zoning codes
    zoning_codes = ['R1', 'R2', 'C1', 'C2', 'M1', 'AG', 'PD']
    # Street names
    streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Washington Blvd', 'Lincoln Way', 
              'Jefferson St', 'Park Ave', 'Lake Dr', 'River Rd', 'Mountain View']
    
    # Generate data for each parcel
    for i in range(count):
        # Address
        street_num = np.random.randint(100, 9999)
        street = np.random.choice(streets)
        address = f"{street_num} {street}"
        data['Address'].append(address)
        
        # City
        city = np.random.choice(cities)
        data['City'].append(city)
        
        # Zip Code (5-digit)
        zip_code = np.random.randint(90000, 96000)
        data['ZipCode'].append(zip_code)
        
        # Land Use
        land_use = np.random.choice(land_uses)
        data['LandUse'].append(land_use)
        
        # Zoning Code
        zoning_code = np.random.choice(zoning_codes)
        data['ZoningCode'].append(zoning_code)
        
        # Acres (0.1 to 10 acres)
        acres = round(np.random.uniform(0.1, 10.0), 2)
        data['Acres'].append(acres)
        
        # Assessed Value ($100K to $2M)
        assessed_value = np.random.randint(100000, 2000000)
        data['AssessedValue'].append(assessed_value)
        
        # Sale Date (within last 10 years)
        days_back = np.random.randint(0, 3650)
        sale_date = pd.Timestamp.now() - pd.Timedelta(days=days_back)
        data['SaleDate'].append(sale_date.strftime('%Y-%m-%d'))
        
        # Sale Price (80% to 120% of assessed value)
        price_factor = np.random.uniform(0.8, 1.2)
        sale_price = int(assessed_value * price_factor)
        data['SalePrice'].append(sale_price)
        
        # Year Built (1950 to 2023)
        year_built = np.random.randint(1950, 2024)
        data['YearBuilt'].append(year_built)
        
        # Square Feet (based on acres, roughly)
        sq_ft = int(acres * 43560 * np.random.uniform(0.1, 0.3))  # 10-30% lot coverage
        data['SquareFeet'].append(sq_ft)
        
        # Bedrooms and Bathrooms (for residential only)
        if land_use == 'Residential':
            bedrooms = np.random.randint(1, 6)
            bathrooms = np.random.randint(1, 4)
        else:
            bedrooms = 0
            bathrooms = 0
        data['Bedrooms'].append(bedrooms)
        data['Bathrooms'].append(bathrooms)
        
        # Generate a random polygon for the parcel
        # Random offset from base coordinates
        lat_offset = np.random.uniform(-0.5, 0.5)
        lon_offset = np.random.uniform(-0.5, 0.5)
        
        center_lat = base_lat + lat_offset
        center_lon = base_lon + lon_offset
        
        # Scale for parcel size (larger for larger acreage)
        scale = 0.001 * np.sqrt(acres)
        
        # Create a simple polygon
        if np.random.random() < 0.7:  # 70% are simple rectangles
            # Rectangle
            points = [
                (center_lon - scale, center_lat - scale),
                (center_lon + scale, center_lat - scale),
                (center_lon + scale, center_lat + scale),
                (center_lon - scale, center_lat + scale),
                (center_lon - scale, center_lat - scale)  # Close the polygon
            ]
        else:
            # More complex polygon (random hexagon)
            points = []
            for j in range(6):
                angle = j * (2 * np.pi / 6)
                # Add some randomness to the shape
                rand_scale = scale * np.random.uniform(0.8, 1.2)
                x = center_lon + rand_scale * np.cos(angle)
                y = center_lat + rand_scale * np.sin(angle)
                points.append((x, y))
            # Close the polygon
            points.append(points[0])
        
        # Create a Shapely polygon and convert to WKT
        polygon = Polygon(points)
        wkt = wkt_dumps(polygon)
        data['geometry'].append(wkt)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    return df

def save_test_data(df, output_dir='uploads', filename='test_parcels.csv'):
    """
    Save the test data to a CSV file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save
        output_dir (str): Directory to save the file in
        filename (str): Name of the file
        
    Returns:
        str: Path to the saved file
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the file
    output_path = os.path.join(output_dir, filename)
    df.to_csv(output_path, index=False)
    
    return output_path

if __name__ == '__main__':
    # Example usage
    test_df = generate_test_parcel_data(count=50)
    output_path = save_test_data(test_df)
    print(f"Generated test data saved to {output_path}")
    print(f"Number of records: {len(test_df)}")
    print(f"Columns: {', '.join(test_df.columns)}")