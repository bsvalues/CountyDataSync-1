# CountyDataSync Packaging Guide

This guide explains how to package CountyDataSync as a standalone executable for distribution.

## Prerequisites

Before packaging, make sure you have installed:

1. PyInstaller: `pip install pyinstaller`
2. All required dependencies for CountyDataSync

## Packaging Process

### Step 1: Prepare the Environment

Ensure all dependencies and required files are present:

```bash
# Verify all required packages are installed
pip install -r requirements.txt

# Create necessary directories
mkdir -p build dist logs output
```

### Step 2: Generate an Icon (Optional)

The packaging script will automatically generate an icon, but you can also create one manually:

```bash
python generate_icon.py
```

### Step 3: Build the Executable

The build process is handled by the `build_executable.py` script:

```bash
python build_executable.py
```

This script:
1. Checks for PyInstaller and other prerequisites
2. Generates a PyInstaller spec file (if not present)
3. Runs PyInstaller to build the executable
4. Reports the path to the created executable

The executable will be created in the `dist` directory.

## Packaging Options

### Customizing the Build

To customize the build, edit the `generate_spec.py` file:

- Change included modules in the `hiddenimports` section
- Modify included data files in the `datas` section
- Change the executable name (default is 'CountyDataSync')

### Creating Platform-Specific Packages

The packaging script will automatically create the correct type of executable for your platform:
- Windows: `.exe` file
- macOS: `.app` bundle
- Linux: executable file

## Running the Packaged Application

The packaged application can be run directly:

```bash
# Windows
dist\CountyDataSync.exe

# macOS/Linux
./dist/CountyDataSync
```

### Command-Line Arguments

The packaged application supports the same command-line arguments as the script:

```bash
# Get help
./dist/CountyDataSync --help

# Use test data instead of SQL Server
./dist/CountyDataSync --test-data

# Specify batch size and output directory
./dist/CountyDataSync --batch-size 2000 --output-dir /path/to/output

# Enable verbose logging
./dist/CountyDataSync --verbose
```

## Troubleshooting

If you encounter issues with the packaged executable:

1. Check the logs in the `logs` directory
2. Verify all dependencies are correctly specified in the spec file
3. Run with the `--verbose` flag for more detailed logging
4. Ensure all required data files are included in the spec file

## Distributing the Package

The standalone executable should be distributed with:

1. Any configuration files (if not embedded)
2. Instructions for setting environment variables (if needed)
3. Documentation (README, user guide, etc.)

## Maintenance

When updating the application:

1. Update the version number in the code
2. Rebuild the package using the steps above
3. Test the package thoroughly before distribution

## Deployment Checklist

Before deploying the packaged application:

- [ ] Test the executable on a clean system
- [ ] Verify all features work correctly
- [ ] Check that log files are created correctly
- [ ] Ensure output files can be written to the specified directory
- [ ] Test database connections (if applicable)
- [ ] Verify command-line arguments work as expected