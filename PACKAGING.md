# CountyDataSync Packaging Guide

This guide explains how to package the CountyDataSync ETL service as a standalone executable using PyInstaller.

## Prerequisites

- Python 3.7+ installed
- CountyDataSync code repository
- Required packages installed

## Step 1: Prepare Your Environment

Before packaging, ensure your environment is properly configured:

1. Verify application functionality:
   ```
   python sync.py --test-data
   ```
   
2. Check environment variables

## Step 2: Install PyInstaller

```
pip install pyinstaller
```

## Step 3: Package the Application

Option 1: Use the generator script (Recommended)
```
python generate_spec.py
python build_executable.py
```

Option 2: Direct PyInstaller command
```
pyinstaller --onefile sync.py
```

## Step 4: Test the Executable

1. Navigate to the dist directory
2. Run the executable with test data
3. Verify functionality

## Step 5: Deployment

1. Copy the executable to the target system
2. Set up environment variables
3. Create required directories
4. Run the executable

## Troubleshooting

- Check for missing modules
- Verify environment variables
- Test database connectivity
- Enable debug logging