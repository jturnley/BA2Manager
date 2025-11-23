# Quick Start Guide

## Running the Application

### First Time Setup

1. **Activate the virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Run the application:**
   ```powershell
   python -m ba2_manager.main
   ```

### Configure Settings

When you first run the application:

1. Go to the **Settings** tab
2. Click "Browse" for each path:
   - **Archive2.exe Path**: Point to your Archive2.exe
     - (Usually in `CreationKit\Tools\Archive2` or `Fallout4\Tools\Archive2`)
   - **MO2 Mods Directory**: Select your `MO2\mods` folder
   - **Fallout 4 Path**: Select your Fallout 4 installation folder
3. Click **Save Settings**

### Using the Application

#### Count BA2 Files
1. Go to "Count BA2 Files" tab
2. Configure Fallout 4 path in Settings first
3. Click "Refresh Count" to see total BA2 file count
4. View breakdown: Base Game | Mods | Creation Club

#### Extract BA2 Mods
1. Go to "Manage BA2 Mods" tab
2. Ensure MO2 directory is configured
3. Select a mod from the list or click "Extract All"
4. Monitor progress and status updates

#### Manage Creation Club
1. Go to "Creation Club" tab
2. Select CC packages
3. Click "Enable Selected" or "Disable Selected"
4. Check status for confirmation

#### View Operation Logs
1. Go to "Logs" tab
2. Click "Refresh Logs" to see recent operations
3. Use "Clear Logs" to reset log file

## Development

### Running Tests
```powershell
pytest
```

### Code Formatting
```powershell
black ba2_manager tests
```

### Linting
```powershell
ruff check ba2_manager tests
```

## Building a Standalone Executable

1. **Install PyInstaller dependencies:**
   ```powershell
   pip install PyInstaller
   ```

2. **Build the executable:**
   ```powershell
   pyinstaller ba2_manager.spec
   ```

3. **Executable location:**
   - `dist\ba2-manager\ba2-manager.exe`

4. **Run directly:**
   - No Python installation needed on the target system
   - All dependencies are bundled

## Troubleshooting

### "Archive2.exe Not Found"
- Download from Fallout 4 Creation Kit or your Fallout 4 installation
- Ensure path is set correctly in Settings

### "Module not found" errors
- Activate virtual environment: `.venv\Scripts\Activate.ps1`
- Reinstall dependencies: `pip install -e ".[dev]"`

### GUI won't start
- Check that PyQt6 is installed: `pip list | grep PyQt`
- Reinstall if needed: `pip install PyQt6 --upgrade`

### Permission errors when extracting
- Close any open files from the BA2 you're extracting
- Check that MO2 directory is accessible
- Run with appropriate permissions

## Project Structure at a Glance

```
Core Functionality:
  ba2_manager/core/ba2_handler.py    ← All BA2 operations
  ba2_manager/config.py               ← Settings storage

User Interface:
  ba2_manager/gui/main_window.py      ← 5-tab GUI
  ba2_manager/main.py                 ← App launcher

Configuration:
  pyproject.toml                      ← Python packaging
  ba2_manager_config.json             ← User settings (auto-created)
  ba2-manager.log                     ← Operation logs
```

## Common Tasks

### Extract all BA2s
1. Settings tab → Configure Archive2.exe path
2. Manage BA2 Mods tab → Click "Extract All"
3. Wait for completion (check status)

### Restore BA2s
1. Select BA2 in list
2. Click "Restore Selected"
3. Original BA2 will be repacked from loose files

### Check BA2 Count
1. Settings tab → Configure Fallout 4 path
2. Count BA2 Files tab → "Refresh Count"
3. See breakdown of all BA2 files

## Tips & Best Practices

- **Always backup** mod folders before extracting
- **Check logs** after operations for any errors
- **Monitor progress** on large extractions (100+ GB)
- **Use batch operations** for multiple files when possible
- **Save settings** after configuring paths

## Keyboard Shortcuts

(Coming in future versions)

## Getting Help

1. Check `README.md` for detailed documentation
2. Review operation logs in Logs tab
3. Verify all paths in Settings tab
4. Ensure Archive2.exe is accessible

---

**Ready to manage BA2 files!**
