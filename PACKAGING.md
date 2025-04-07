# Packaging CountyDataSync Application

This guide provides instructions for packaging the CountyDataSync application into a standalone executable using PyInstaller. This allows users to run the application without installing Python or any dependencies.

## Prerequisites

Before packaging the application, ensure you have:

1. A working development environment with all dependencies installed
2. PyInstaller installed (`pip install pyinstaller`)
3. Completed basic testing to ensure the application works as expected

## Step 1: Generate the Application Icon

The application includes a script to generate a custom icon. Run:

```bash
python generate_icon.py
```

This will create `generated-icon.png` in the root directory of the project.

## Step 2: Generate the PyInstaller Specification File

The application includes a script to generate the PyInstaller spec file:

```bash
python generate_spec.py
```

This will create `sync_executable.spec` in the root directory, which contains the packaging configuration for PyInstaller.

## Step 3: Build the Executable

Run the build_executable.py script to create the standalone executable:

```bash
python build_executable.py
```

This will:
1. Compile the Python code and dependencies
2. Package them into a standalone executable
3. Place the executable in the `dist` directory

The process might take several minutes to complete depending on your system.

## Step 4: Verify the Executable

After building, you should find the executable in the `dist` directory:

- Windows: `dist/CountyDataSync.exe`
- macOS: `dist/CountyDataSync`
- Linux: `dist/CountyDataSync`

Test the executable to ensure it works correctly:

```bash
# On Windows
dist\CountyDataSync.exe

# On macOS/Linux
./dist/CountyDataSync
```

## Step 5: Distribute the Application

You can distribute the executable to users by:

1. Compressing the executable file (and any necessary assets)
2. Uploading to a shared drive or file-sharing service
3. Creating an installer using tools like NSIS (Windows), DMG Creator (macOS), or AppImage (Linux)

### Optional: Create an Installer

For a more professional distribution, consider creating an installer:

- **Windows**: Use [NSIS](https://nsis.sourceforge.io/) or [Inno Setup](https://jrsoftware.org/isinfo.php)
- **macOS**: Create a DMG file using `hdiutil`
- **Linux**: Create an AppImage or Snap package

## Troubleshooting

If you encounter issues during packaging:

1. **Missing dependencies**: Modify the spec file to include hidden imports
2. **File not found errors**: Ensure all data files are included in the spec file
3. **Application crashes**: Run with debug mode enabled using the `--debug` flag

### Common Issues

#### Hidden Imports

If your application uses dynamic imports, you may need to explicitly include them in the spec file:

```python
hiddenimports=['pandas', 'geopandas', 'pyodbc'],
```

#### Data Files

Make sure all required data files are included by adding them to the spec file:

```python
datas=[
    ('config.py', '.'),
    ('templates', 'templates'),
    ('static', 'static'),
],
```

## Continuous Integration

For automated builds, you can integrate the packaging process in your CI/CD pipeline:

1. Install PyInstaller in your CI environment
2. Run the packaging script as part of your build process
3. Capture the executable as an artifact

See the CI_CD_GUIDE.md file for more detailed instructions on setting up continuous integration.

## Environment-specific Configuration

The packaged application reads configuration from environment variables. Users will need to set these variables before running the executable:

```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://user:password@localhost/database"
$env:USE_TEST_DATA="false"

# macOS/Linux
export DATABASE_URL="postgresql://user:password@localhost/database"
export USE_TEST_DATA="false"
```

Alternatively, you can create a .env file in the same directory as the executable.

## Security Considerations

When packaging your application:

1. Do not include sensitive credentials in the packaged application
2. Use environment variables or secure credential storage for sensitive information
3. Sign your executable if possible to prevent tampering

By following these steps, you'll be able to create a professional, self-contained executable version of CountyDataSync that can be easily distributed to users.