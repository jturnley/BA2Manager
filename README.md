# BA2 Manager v2.0.0

A comprehensive Python application for managing Fallout 4 BA2 archive files through Mod Organizer 2. This project recreates and enhances the functionality of the PowerShell `manage_ba2_pro.ps1` script as a professional cross-platform GUI application.

## Features

### Core Functionality
- **Smart BA2 Counting**: Separate tracking for Main BA2s (0-255 limit) and Texture BA2s (0-254 limit) with color-coded progress bars that turn red when limits are exceeded
- **Active Mods Only**: Counts only mods enabled in MO2's modlist.txt, respecting disabled mods and disabled plugins
- **Granular BA2 Management**: Extract/restore individual Main or Texture BA2s independently per mod
- **Loose File Cleanup**: Automatically removes extracted loose files when all BA2s are restored (critical for Fallout 4 as loose files override BA2 contents)
- **Load Order Protection**: Automatic backup of modlist.txt and plugins.txt on startup; never modifies load order during normal operations
- **Real-time CC Monitoring**: Detects Creation Club enable/disable events and updates BA2 counts immediately
- **Nexus Mod Integration**: Automatically detects Nexus Mod IDs from `meta.ini` and provides direct clickable links
- **Creation Club Management**: Enable/disable CC content with automatic Fallout4.ccc updates
- **Atomic Operations**: Extractions use temporary directories to prevent partial failures
- **Backup Preservation**: Restore operations preserve backups until all BA2s are restored
- **Custom MO2 Directories**: Automatically detects custom mod_directory settings from ModOrganizer.ini
- **Multiple Profile Support**: Automatically uses the selected MO2 profile when multiple profiles exist
- **Comprehensive Logging**: Detailed operation logs with configurable debug mode
- **Configuration Management**: Auto-detection and persistent storage of all paths

### Advantages Over PowerShell Script
- **Cross-platform GUI**: Modern PyQt6 interface works on Windows, Linux, and macOS
- **Safer Operations**: Atomic extractions, backup preservation, load order protection
- **Better UX**: Single-selection tables, visual progress indicators, real-time feedback
- **Persistent State**: Tracks extraction status across sessions
- **Standalone Executable**: No Python installation required for Windows users
- **Real-time Monitoring**: File watcher detects CC changes immediately

## Related Projects

### CC-Packer - Standalone CC Archive Merger

For a simpler, focused tool to merge Creation Club archives, check out **[CC-Packer](https://github.com/jturnley/CC-Packer)** - our companion tool:

- Merges all CC BA2 files into unified archives
- Reduces plugin count from 70+ to 1
- Improves game load times by 10-30%
- Automatic texture splitting to prevent crashes
- Simple one-click operation

**When to use which tool:**
- Use **CC-Packer** for quick CC content merging
- Use **BA2 Manager** for advanced archive operations, conflict detection, and batch processing

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

Main interface for BA2 operations. Integrates with Archive2.exe and provides comprehensive file management.

**Key Methods:**

- `count_ba2_files(fo4_path)` - Count and categorize all BA2s (Main, DLC, CC, Creation Store, Mods, Texture variants)
- `list_ba2_mods()` - List mods with BA2 info, extraction status, Nexus URLs
- `extract_mod(mod_name)` - Extract all BA2s for a mod (creates backup, uses temp dir)
- `restore_mod(mod_name)` - Restore mod from backup (preserves backup for reuse)
- `extract_mod_ba2(mod_name, ba2_type)` - Extract specific Main or Texture BA2
- `restore_mod_ba2(mod_name, ba2_type)` - Restore specific Main or Texture BA2
- `get_cc_packages(fo4_path)` - List all CC content with enabled status
- `write_ccc_file(fo4_path, enabled_plugins)` - Update Fallout4.ccc and reposition CC content
- `backup_modlist()` / `backup_plugins()` - Create .bak files for load order protection
- `get_log_entries(lines)` - Retrieve recent log entries

**Example Usage:**

```python
from ba2_manager.core.ba2_handler import BA2Handler

handler = BA2Handler(
    archive2_path="C:\\Path\\To\\Archive2.exe",
    mo2_dir="C:\\MO2\\mods",
    backup_dir="C:\\MO2\\BA2_Manager_Backups",
    log_file="ba2-manager.log"
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
  "log_file": "ba2-manager.log",
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

