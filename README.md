# BA2 Manager Pro v1.0.0

A comprehensive Python application for managing Fallout 4 BA2 archive files. This project recreates and enhances the functionality of the PowerShell `manage_ba2_pro.ps1` script as a professional GUI application.

## Features

### Core Functionality
- **Count BA2 Files**: View total BA2 count including base game, mods, and Creation Club content.
- **Manage BA2 Mods**: Extract and restore BA2 files to manage Fallout 4's 255 BA2 file limit.
- **Nexus Mod Links**: Automatically detects Nexus Mod IDs from `meta.ini` and provides direct links to mod pages.
- **Manage Creation Club Content**: Enable/disable Creation Club (CC) content with a checkbox interface.
- **View Extraction Logs**: Review detailed operation logs.
- **Configuration Management**: Store and manage paths to Archive2.exe, MO2, and Fallout 4 installations.

### Advantages Over PowerShell Script
- **Cross-platform GUI**: Modern PyQt6 interface with sortable tables and direct links.
- **Persistent Configuration**: Settings are saved automatically.
- **Real-time Progress**: Visual feedback during extraction/restoration.
- **Standalone Executable**: No Python installation required for end users.
- **Safety Features**: Backup system for extracted mods and validation checks.

## Installation & Usage

### For End Users (Standalone Executable)
1. Download the latest release (`ba2-manager.exe`) from the Releases page.
2. Place the executable anywhere (e.g., inside your MO2 folder).
3. Run `ba2-manager.exe`.
4. On first run, configure your paths in the **Settings** tab:
   - **MO2 Mods Directory**: Where your mods are installed.
   - **Archive2.exe Path**: Required for extraction (usually in `Fallout 4/Tools/Archive2`).
   - **Fallout 4 Path**: Your game installation folder.

### For Developers (Python Setup)

```bash
# Clone the repository
git clone https://github.com/jturnley/BA2Manager.git
cd BA2Manager

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -e .
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
| `Manage-CreationClub` | `BA2Handler.enable/disable_cc_content()` | ✅ Implemented |
| `View-Log` | `BA2Handler.get_log_entries()` | ✅ Implemented |
| `Show-Menu` | `MainWindow` tabs | ✅ Implemented |
| `Get-NexusLink` | `BA2Handler._get_nexus_url()` | ✅ Implemented |

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

