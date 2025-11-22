# BA2 Manager Pro

A comprehensive Python application for managing Fallout 4 BA2 archive files. This project recreates the functionality of the PowerShell `manage_ba2_pro.ps1` script as a professional GUI application with a cleaner, more extensible codebase.

## Features

### Core Functionality (From PowerShell Script)
- **Count BA2 Files**: View total BA2 count including base game, mods, and Creation Club content
- **Manage BA2 Mods**: Extract and restore BA2 files to manage Fallout 4's 255 BA2 file limit
- **Manage Creation Club Content**: Enable/disable Creation Club (CC) content
- **View Extraction Logs**: Review detailed operation logs
- **Configuration Management**: Store and manage paths to Archive2.exe, MO2, and Fallout 4 installations

### Advantages Over PowerShell Script
- Cross-platform GUI (Windows, macOS, Linux)
- Persistent configuration storage
- Real-time progress tracking
- Standalone executable (no Python installation required for end users)
- Better error handling and user feedback
- Extensible architecture for future improvements

## Installation & Setup

### Development Setup

```bash
# Clone or navigate to the project
cd "BA2 Manager"

# Create virtual environment (if not already done)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install in development mode with dependencies
pip install -e ".[dev]"
```

### Running the Application

```bash
# Run directly
python -m ba2_manager.main

# Or use the module
ba2-manager
```

## Project Structure

```
ba2-manager/
├── ba2_manager/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── gui/                 # GUI components
│   │   ├── __init__.py
│   │   └── main_window.py   # Main PyQt6 application window
│   ├── core/                # Core BA2 operations
│   │   ├── __init__.py
│   │   └── ba2_handler.py   # BA2 file handling & Archive2 integration
│   └── resources/           # Application resources (icons, etc)
├── tests/                   # Unit tests
│   ├── __init__.py
│   └── test_ba2_handler.py  # BA2 handler tests
├── pyproject.toml           # Project configuration
├── requirements-dev.txt     # Development dependencies
├── ba2_manager.spec         # PyInstaller specification
└── README.md                # This file
```

## Module Documentation

### `ba2_manager.core.ba2_handler` - BA2Handler Class

Main interface for BA2 operations. Wraps Archive2.exe functionality and provides file management capabilities.

**Key Methods:**

- `count_ba2_files(fo4_path)` - Count total BA2s (base game + mods + CC)
- `list_ba2_mods()` - List all BA2 mods in MO2 directory
- `extract_ba2_file(ba2_path, output_dir)` - Extract BA2 using Archive2.exe
- `repack_ba2_file(source_dir, output_ba2)` - Repack loose files into BA2
- `enable_cc_content(plugin_base)` - Enable Creation Club content
- `disable_cc_content(plugin_base)` - Disable Creation Club content
- `get_log_entries(lines)` - Retrieve recent log entries

**Example Usage:**

```python
from ba2_manager.core.ba2_handler import BA2Handler

handler = BA2Handler(
    archive2_path="C:\\Path\\To\\Archive2.exe",
    mo2_dir="C:\\MO2\\mods",
    log_file="BA2_Extract.log"
)

# Count BA2s
counts = handler.count_ba2_files("C:\\Fallout4")
print(f"Total BA2s: {counts['total']}/255")

# Extract a BA2 file
success = handler.extract_ba2_file("C:\\MO2\\mods\\MyMod\\archive.ba2")
```

### `ba2_manager.config` - Config Class

Manages persistent configuration storage in JSON format.

**Key Methods:**

- `load_config()` - Load settings from file
- `save_config()` - Save settings to file
- `get(key, default)` - Get configuration value
- `set(key, value)` - Set and save configuration value
- `update(values)` - Update multiple values

**Example Usage:**

```python
from ba2_manager.config import Config

config = Config()
config.set("archive2_path", "C:\\CreationKit\\Archive2.exe")
archive2 = config.get("archive2_path")
```

### `ba2_manager.gui.main_window` - MainWindow Class

PyQt6 GUI application with tabbed interface.

**Tabs:**
1. **Count BA2 Files** - View BA2 count statistics
2. **Manage BA2 Mods** - Extract/restore BA2 files with progress tracking
3. **Creation Club** - Enable/disable CC content
4. **Logs** - View and manage operation logs
5. **Settings** - Configure paths and preferences

## Requirements

- **Python**: 3.12+ (latest stable)
- **Archive2.exe**: Required for BA2 extraction/repacking
  - Source: Fallout 4 Creation Kit or Fallout 4 installation
- **Mod Organizer 2**: For mod management (optional for other features)

## Dependency on PowerShell Script Components

This application recreates all major functions from `manage_ba2_pro.ps1`:

| PowerShell Function | Python Equivalent | Status |
|---|---|---|
| `Count-BA2Files` | `BA2Handler.count_ba2_files()` | ✅ Implemented |
| `Manage-BA2Mods` | `BA2Handler.extract/repack` | ✅ Implemented |
| `Manage-CreationClub` | `BA2Handler.enable/disable_cc_content()` | ✅ Skeleton |
| `View-Log` | `BA2Handler.get_log_entries()` | ✅ Implemented |
| `Show-Menu` | `MainWindow` tabs | ✅ Implemented |

## Configuration

Settings are stored in `ba2_manager_config.json`:

```json
{
  "archive2_path": "C:\\CreationKit\\Archive2.exe",
  "mo2_mods_dir": "C:\\MO2\\mods",
  "fo4_path": "C:\\Program Files\\Fallout4",
  "log_file": "BA2_Extract.log",
  "backup_dir": "./mod_backups"
}
```

## Building Standalone Executable

```bash
# Install PyInstaller (included in dev dependencies)
pip install PyInstaller

# Build executable
pyinstaller ba2_manager.spec

# Executable will be in dist/ba2-manager/
```

The resulting executable bundles Python 3.12 and all dependencies, requiring no Python installation on the target system.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ba2_manager tests/

# Run specific test file
pytest tests/test_ba2_handler.py
```

## Development

### Code Quality

```bash
# Format code
black ba2_manager tests

# Lint
ruff check ba2_manager tests

# Type checking (if mypy is installed)
mypy ba2_manager
```

### Adding Features

The modular structure makes it easy to add features:

1. Add handler methods to `BA2Handler` in `core/ba2_handler.py`
2. Create GUI components in `gui/` as needed
3. Add corresponding tabs or dialogs to `main_window.py`
4. Write tests in `tests/`

## Troubleshooting

### Archive2.exe Not Found
- Place `Archive2.exe` in MO2 directory, or
- Configure path in Settings tab, or
- Install from Fallout 4 Creation Kit

### BA2 File Errors
- Ensure BA2 files are not locked by other applications
- Check file permissions and disk space
- Review logs for detailed error messages

### Performance Issues
- Extraction of large BA2 files may take time
- Monitor Archive2.exe process for CPU/disk usage
- Consider extracting smaller batches first

## License

MIT License - See LICENSE file for details

## Credits

Original PowerShell script concept by Illrigger
Python application rewrite with enhanced features

## Support

For issues, questions, or feature requests, refer to the project documentation or examine logs in the application.

