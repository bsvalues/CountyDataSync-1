# CountyDataSync Packaging Guide

This guide explains how to package the CountyDataSync ETL service as a standalone executable using PyInstaller.

## Prerequisites

- Python 3.7+ installed on your system
- CountyDataSync code repository
- Required packages installed

## Step 1: Prepare Your Environment

Before packaging, ensure your local development environment is properly configured.

## Step 2: Generate Spec File

Create a PyInstaller spec file that defines how to package your application:

1. Run the generator script:
   `python generate_spec.py`
   
   This creates sync_executable.spec with the proper configuration.

## Step 3: Build the Executable

1. Run the build script:
   `python build_executable.py`
   
2. The packaged executable will be in the dist directory.

## Step 4: Test the Executable

Run and verify the executable works as expected.

## Step 5: Deployment

Copy the executable and required files to the target system, and follow the installation guide.

## Troubleshooting

Check the logs for detailed error information.
