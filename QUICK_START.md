# Quick Start Guide - BA2 Manager Pro v1.1.3

## Running the Application

### For End Users (Windows Executable)

1. **Download** `ba2-manager.exe` from Releases
2. **Place** anywhere (recommended: inside MO2 directory for portability)
3. **Run** `ba2-manager.exe`
4. **Configure** paths on first run (see below)

### For Developers (Python)

1. **Activate the virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Run the application:**
   ```powershell
   python -m ba2_manager.main
   ```

## Initial Configuration

On first run, the app will attempt to auto-detect paths. If needed, manually configure:

### Settings Tab

1. **Click "Find ModOrganizer.exe"** button
   - Automatically detects: MO2 mods directory, Fallout 4 path, Archive2.exe
   - Sets up backup directory location
   - **Recommended method** for easiest setup

2. **Or manually configure paths:**
   - **Archive2.exe**: Usually in `Fallout4\Tools\Archive2` or `CreationKit\Tools\Archive2`
   - **MO2 Mods Directory**: Your `ModOrganizer2\mods` folder
   - **Fallout 4 Path**: Your Fallout 4 installation folder

3. **Click "Save Settings"**

**Note**: BA2 Manager automatically:
- Creates backups of `modlist.txt` and `plugins.txt` on startup
- Detects custom mod directories from `ModOrganizer.ini`
- Only counts active mods (enabled in modlist.txt and plugins.txt)

## Using the Application

### BA2 Info Tab (Default View)

**Dual Progress Bars:**
- **Main BA2s**: 0-255 limit (green = safe, red blinking = over limit)
- **Texture BA2s**: 0-254 limit (green = safe, red blinking = over limit)

**Category Breakdown:**
- Base Game (Main + DLC)
- Creation Club (active only)
- Creation Store
- Mods (active only)
- Vanilla Replacements

**Actions:**
- Click "Refresh Count" to update statistics
- Watch progress bars for limit warnings

### Manage Mods Tab

**View Mods:**
- Table shows: Mod Name | Main BA2 | Texture BA2 | Nexus Link
- Green checkboxes = Already extracted (loose files)
- Empty checkboxes = Packed (BA2 archives)
- Click Nexus link to open mod page in browser

**Extract BA2s:**
1. Click checkbox for Main and/or Texture BA2 to extract
2. Multiple mods can be selected
3. Click **"Apply Actions"** button
4. Atomic extraction creates backup automatically

**Restore BA2s:**
1. Uncheck the Main and/or Texture BA2 checkboxes
2. Click **"Apply Actions"**  
3. Restores from backup (backup is preserved for reuse)

**Restore All:**
- Click "Restore All Extracted" to revert all mods to BA2 archives
- Useful for quick cleanup

### Manage Creation Club Tab

**Enable/Disable CC Content:**
1. Check boxes for CC content you want enabled
2. Uncheck boxes for CC content you want disabled
3. Click **"Apply Changes"**

**Smart Repositioning:**
- BA2 Manager intelligently repositions enabled CC plugins and mods
- Maintains alphabetical order among CC/DLC content
- Prevents random repositioning when MO2 disables CC content
- **This is the ONLY operation that modifies modlist.txt or plugins.txt**

**Bulk Actions:**
- "Enable All" - Activate all CC content
- "Disable All" - Deactivate all CC content

### View Logs Tab

- Shows recent operation logs
- Click "Refresh" to update
- Useful for troubleshooting errors

## Load Order Protection

BA2 Manager Pro **automatically protects your load order**:

- **Automatic Backups**: Creates `.bak` files for `modlist.txt` and `plugins.txt` on startup
- **Atomic Operations**: Extraction/restoration uses temporary directories
- **Backup Preservation**: Restoring a mod does NOT delete backups (can restore again)
- **Smart CC Repositioning**: Only CC content is repositioned alphabetically (mods untouched)

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

### CC Content Not Repositioning

- BA2 Manager only repositions when you click "Apply Changes" in Manage CC tab
- Repositioning is smart: maintains alphabetical order among CC/DLC
- Regular mod order is NEVER modified

## Tips

- **Always backup your MO2 directory** before major changes
- Use "Restore All Extracted" for quick cleanup
- Check logs for detailed error messages
- Backups are preserved - you can restore the same mod multiple times
- BA2 Manager only modifies load order files when managing CC content
- Granular extraction lets you extract Main OR Texture independently

## Project Structure at a Glance

```plaintext
Core Functionality:
  ba2_manager/core/ba2_handler.py    ← All BA2 operations
  ba2_manager/config.py               ← Settings storage

User Interface:
  ba2_manager/gui/main_window.py      ← 4-tab GUI
  ba2_manager/main.py                 ← App launcher

Configuration:
  pyproject.toml                      ← Python packaging
  ba2_manager_config.json             ← User settings (auto-created)
  ba2-manager.log                     ← Operation logs
```

## Common Tasks

### Count All BA2 Files

1. Settings tab → Configure Archive2.exe path
2. BA2 Info tab → Click "Refresh Count"
3. View progress bars (Main 0-255, Texture 0-254)
4. See category breakdown

### Extract Single Mod's BA2

1. Manage Mods tab → Find mod in table
2. Click Main BA2 checkbox OR Texture BA2 checkbox (or both)
3. Click "Apply Actions"
4. Green checkbox indicates extracted state

### Restore Extracted Mod

1. Manage Mods tab → Find extracted mod (green checkboxes)
2. Uncheck Main and/or Texture checkboxes
3. Click "Apply Actions"
4. BA2 files restored from backup

### Manage Creation Club

1. Manage CC tab → Check/uncheck CC content
2. Click "Apply Changes"
3. CC content automatically repositioned alphabetically

## Tips & Best Practices

- **Automatic backups**: modlist.txt and plugins.txt are backed up on app startup
- **Check logs** after operations for detailed information
- **Monitor progress bars**: Red blinking = over limit
- **Granular extraction**: Extract Main OR Texture independently to save space
- **Save settings** after configuring paths
- **Backups preserved**: You can restore the same mod multiple times

## Need More Help?

- Check the **Logs** tab for detailed operation logs
- Review **API_REFERENCE.md** for developer documentation
- See **README.md** for full feature list

## Getting Help

1. Check `README.md` for detailed documentation
2. Review operation logs in Logs tab
3. Verify all paths in Settings tab
4. Ensure Archive2.exe is accessible

---

**Ready to manage BA2 files!**
