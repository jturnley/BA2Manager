# BA2 Manager Pro - API Reference v2.0.0

## BA2Handler Class

Complete reference for the core BA2 operations handler. This class provides all BA2 archive operations, MO2 integration, Creation Club management, load order protection, and BA2 merging capabilities.

### Initialization

```python
from ba2_manager.core.ba2_handler import BA2Handler

handler = BA2Handler(
    archive2_path="C:\\Path\\To\\Archive2.exe",
    mo2_dir="C:\\MO2\\mods",
    fo4_path="C:\\Program Files\\Fallout4",
    log_file="ba2-manager.log"
)
```

**Parameters:**
- `archive2_path` (str): Path to Archive2.exe
- `mo2_dir` (str): Path to MO2 mods directory
- `fo4_path` (str): Path to Fallout 4 installation
- `log_file` (str, optional): Log file path (default: "ba2-manager.log")

**Automatic Actions on Init:**
- Creates backup of `modlist.txt` as `modlist.txt.bak`
- Creates backup of `plugins.txt` as `plugins.txt.bak`
- Detects custom mod directories from `ModOrganizer.ini`
- Initializes logging system

## Core Methods

### BA2 Counting and Information

#### `count_ba2_files() -> Dict[str, Any]`

Count all BA2 files with comprehensive breakdown. **Only counts active mods** (enabled in modlist.txt and plugins.txt).

**Returns:**

```python
{
    "main": {
        "base_game": 10,
        "creation_club": 8,
        "creation_store": 5,
        "mods": 42,
        "vanilla_replacements": 3,
        "total": 68
    },
    "texture": {
        "base_game": 10,
        "creation_club": 7,
        "creation_store": 4,
        "mods": 35,
        "vanilla_replacements": 2,
        "total": 58
    }
}
```

**Example:**

```python
counts = handler.count_ba2_files()
print(f"Main BA2s: {counts['main']['total']}/255")
print(f"Texture BA2s: {counts['texture']['total']}/254")
```

#### `list_ba2_mods() -> List[Dict[str, Any]]`

List all mods with BA2 files. **Returns only active mods** (enabled in modlist.txt).

**Returns:**

List of dictionaries with:

```python
{
    "mod_name": "My Awesome Mod",
    "main_ba2": "MyMod - Main.ba2",
    "texture_ba2": "MyMod - Textures.ba2",
    "has_main": True,
    "has_texture": True,
    "main_extracted": False,
    "texture_extracted": False,
    "nexus_url": "https://nexusmods.com/fallout4/mods/12345"
}
```

**Example:**

```python
mods = handler.list_ba2_mods()
for mod in mods:
    status = "Extracted" if mod["main_extracted"] else "Packed"
    print(f"{mod['mod_name']}: {status}")
```

### Mod Extraction and Restoration

#### `extract_mod(mod_name: str) -> bool`

Extract **all BA2 files** for a mod (both Main and Texture). Uses atomic operations with temporary directories.

**Parameters:**

- `mod_name` (str): Mod folder name

**Returns:**

- `bool`: True if successful

**Features:**

- Atomic extraction (uses temp directory, renames on success)
- Automatically creates backup in `BA2_Manager_Backups/`
- Preserves original BA2 files in backup

**Example:**

```python
if handler.extract_mod("MyAwesomeMod"):
    print("Mod fully extracted!")
```

#### `restore_mod(mod_name: str) -> bool`

Restore **all BA2 files** for a mod from backup. **Does NOT delete backup** (can be restored again).

**Parameters:**

- `mod_name` (str): Mod folder name

**Returns:**

- `bool`: True if successful

**Features:**

- Restores from `BA2_Manager_Backups/`
- Preserves backup folder for reuse
- Copies BA2 files back to mod folder

**Example:**

```python
if handler.restore_mod("MyAwesomeMod"):
    print("Mod BA2s restored!")
```

#### `extract_mod_ba2(mod_name: str, ba2_type: str) -> bool`

**NEW in v1.1.0**: Extract **specific BA2 type** (Main or Texture only). Granular control for disk space management.

**Parameters:**

- `mod_name` (str): Mod folder name
- `ba2_type` (str): Either "main" or "texture"

**Returns:**

- `bool`: True if successful

**Features:**

- Extract Main BA2 independently from Texture BA2
- Uses atomic temp directory operations
- Creates backup only if not already backed up

**Example:**

```python
# Extract only Main BA2 (save space by keeping Texture packed)
if handler.extract_mod_ba2("MyMod", "main"):
    print("Main BA2 extracted, textures still packed!")
```

#### `restore_mod_ba2(mod_name: str, ba2_type: str) -> bool`

**NEW in v1.1.0**: Restore **specific BA2 type** (Main or Texture only). Granular control for repacking.

**Parameters:**

- `mod_name` (str): Mod folder name
- `ba2_type` (str): Either "main" or "texture"

**Returns:**

- `bool`: True if successful

**Features:**

- Restore Main BA2 independently from Texture BA2
- Preserves backup for future restores
- Does NOT delete extracted files

**Example:**

```python
# Restore only Texture BA2 (keep Main extracted for editing)
if handler.restore_mod_ba2("MyMod", "texture"):
    print("Texture BA2 restored, Main files still loose!")
```

### Creation Club Management

#### `write_ccc_file(enabled_plugins: set[str]) -> None`

Update `Fallout4.ccc` and reposition CC content intelligently.

**Parameters:**

- `enabled_plugins` (set[str]): Set of enabled CC plugin names (without .esm/.esl)

**Automatic Actions:**

- Updates `Fallout4.ccc` with enabled plugins
- Calls `_reposition_cc_plugins()` - alphabetically sorts CC/DLC plugins
- Calls `_reposition_cc_mods()` - alphabetically sorts CC mods
- **This is the ONLY method that modifies load order files**

**Example:**

```python
enabled = {"ccbgsfo4001", "ccbgsfo4003", "ccbgsfo4006"}
handler.write_ccc_file(enabled)
# CC content now alphabetically ordered in plugins.txt and modlist.txt
```

#### `list_cc_content() -> List[Dict[str, Any]]`

List all Creation Club content with status.

**Returns:**

List of dictionaries:

```python
{
    "plugin": "ccbgsfo4001-pip boy(paint).esm",
    "mod_name": "ccBGSFO4001-PipBoy(Pip-BoyPaints)",
    "enabled": True
}
```

**Example:**

```python
cc_list = handler.list_cc_content()
for item in cc_list:
    status = "✓" if item["enabled"] else "✗"
    print(f"{status} {item['plugin']}")
```

### Load Order Protection

#### `backup_modlist() -> None`

**NEW in v1.1.0**: Create backup of `modlist.txt` as `modlist.txt.bak`. **Called automatically in `__init__`**.

**Example:**

```python
handler.backup_modlist()  # Creates modlist.txt.bak
```

#### `backup_plugins() -> None`

**NEW in v1.1.0**: Create backup of `plugins.txt` as `plugins.txt.bak`. **Called automatically in `__init__`**.

**Example:**

```python
handler.backup_plugins()  # Creates plugins.txt.bak
```

### Utility Methods

#### `get_log_entries(lines: int = 50) -> List[str]`

Retrieve recent log entries from log file.

**Parameters:**

- `lines` (int): Number of lines to retrieve (default: 50)

**Returns:**

- `List[str]`: List of log entry strings

**Example:**

```python
logs = handler.get_log_entries(100)
for entry in logs:
    print(entry)
```

## Config Class

Configuration management for persistent settings stored in `ba2_manager_config.json`.

### Initialization

```python
from ba2_manager.config import Config

config = Config()  # Uses default: ba2_manager_config.json
# Or specify custom file:
config = Config("custom_config.json")
```

### Methods

#### `load_config() -> Dict[str, Any]`

Load configuration from JSON file. **Called automatically on init**.

**Example:**

```python
config = Config()
settings = config.load_config()
```

#### `save_config(config: Dict[str, Any] = None) -> None`

Save configuration to JSON file.

**Parameters:**

- `config` (dict, optional): Config dict to save (saves current if None)

**Example:**

```python
config.config["archive2_path"] = "C:\\Path\\To\\Archive2.exe"
config.save_config()
```

#### `get(key: str, default: Any = None) -> Any`

Get a configuration value with optional default.

**Parameters:**

- `key` (str): Configuration key
- `default` (Any): Default value if key not found

**Returns:**

- Configuration value or default

**Example:**

```python
archive2 = config.get("archive2_path", "")
```

#### `set(key: str, value: Any) -> None`

Set a configuration value and automatically save to file.

**Parameters:**

- `key` (str): Configuration key
- `value` (Any): Value to set

**Example:**

```python
config.set("fo4_path", "C:\\Program Files\\Fallout4")
```

#### `update(values: Dict[str, Any]) -> None`

Update multiple configuration values at once and save.

**Parameters:**

- `values` (dict): Dictionary of key-value pairs to update

**Example:**

```python
config.update({
    "archive2_path": "C:\\Archive2.exe",
    "mo2_mods_dir": "C:\\MO2\\mods",
    "fo4_path": "C:\\Fallout4"
})
```

## Data Types

### Return Types for `list_ba2_mods()`

Returns list of dictionaries with:

```python
{
    "mod_name": str,           # Mod folder name
    "main_ba2": str,           # Main BA2 filename (or None)
    "texture_ba2": str,        # Texture BA2 filename (or None)
    "has_main": bool,          # Has Main BA2
    "has_texture": bool,       # Has Texture BA2
    "main_extracted": bool,    # Main BA2 is extracted
    "texture_extracted": bool, # Texture BA2 is extracted
    "nexus_url": str           # Nexus Mods URL
}
```

### Return Types for `count_ba2_files()`

Returns nested dictionary:

```python
{
    "main": {
        "base_game": int,
        "creation_club": int,
        "creation_store": int,
        "mods": int,
        "vanilla_replacements": int,
        "total": int
    },
    "texture": {
        "base_game": int,
        "creation_club": int,
        "creation_store": int,
        "mods": int,
        "vanilla_replacements": int,
        "total": int
    }
}
```

## Constants

info = BA2Info(
    path="C:\\MO2\\mods\\MyMod\\archive.ba2",
    size=1024000000,
    mod_name="My Mod",
    is_extracted=False,
    file_count=0
)

print(f"{info.mod_name}: {info.size / 1024 / 1024:.1f} MB")
```

---

## Best Practices

### Load Order Protection

BA2 Manager Pro automatically protects your load order:

- **Automatic backups**: `modlist.txt.bak` and `plugins.txt.bak` created on startup
- **Atomic operations**: Extractions use temporary directories
- **Backup preservation**: Restoring does NOT delete backups (can restore multiple times)
- **Minimal modifications**: Only CC management modifies load order files

### Granular BA2 Management

Extract Main or Texture BA2s independently:

```python
# Extract only Main BA2 (saves disk space)
handler.extract_mod_ba2("MyMod", "main")

# Later, restore only Main BA2 (keep textures loose for editing)
handler.restore_mod_ba2("MyMod", "main")
```

### Error Handling

All methods log errors automatically:

```python
if not handler.extract_mod("MyMod"):
    logs = handler.get_log_entries(50)
    print("Last 50 log entries:")
    for entry in logs:
        print(entry)
```

### Active Mod Filtering

BA2 Manager only counts/lists **active mods**:

- Must be enabled in `modlist.txt`
- Plugin must be enabled in `plugins.txt`
- Disabled mods are ignored

This ensures accurate BA2 limits:

```python
counts = handler.count_ba2_files()
# Only counts mods that Fallout 4 will actually load
```

## Logging

All operations are automatically logged to `ba2-manager.log`:

```python
# Log format: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE

# View logs programmatically
logs = handler.get_log_entries(50)
for entry in logs:
    print(entry)
```

## Default Configuration

**File**: `ba2_manager_config.json` (auto-created)

```json
{
  "archive2_path": "",
  "mo2_mods_dir": "./mods",
  "fo4_path": "",
  "log_file": "ba2-manager.log",
  "backup_dir": "BA2_Manager_Backups"
}
```

## Complete Example

Full workflow demonstrating v1.1.0 features:

```python
from ba2_manager.core.ba2_handler import BA2Handler
from ba2_manager.config import Config

# Setup
config = Config()
handler = BA2Handler(
    archive2_path=config.get("archive2_path"),
    mo2_dir=config.get("mo2_mods_dir"),
    fo4_path=config.get("fo4_path")
)
# Automatic: modlist.txt.bak and plugins.txt.bak created

# Count BA2s (only active mods)
counts = handler.count_ba2_files()
main_total = counts["main"]["total"]
texture_total = counts["texture"]["total"]

print(f"Main BA2s: {main_total}/255")
print(f"Texture BA2s: {texture_total}/254")

if main_total > 255 or texture_total > 254:
    print("WARNING: Over BA2 limit!")
    
    # List all active mods with BA2s
    mods = handler.list_ba2_mods()
    for mod in mods:
        print(f"{mod['mod_name']}:")
        print(f"  Main: {mod['has_main']} (extracted: {mod['main_extracted']})")
        print(f"  Texture: {mod['has_texture']} (extracted: {mod['texture_extracted']})")
    
    # Granular extraction (Main only, save space)
    if handler.extract_mod_ba2("MyHeavyMod", "main"):
        print("Main BA2 extracted, textures still packed!")
    
    # Full mod extraction
    if handler.extract_mod("AnotherMod"):
        print("Both BA2s extracted!")

# Creation Club management
cc_list = handler.list_cc_content()
enabled_plugins = {item["plugin"].replace(".esm", "").replace(".esl", "") 
                   for item in cc_list if item["enabled"]}

# Add/remove CC content
enabled_plugins.add("ccbgsfo4001")
enabled_plugins.discard("ccbgsfo4003")

# Smart repositioning (only time load order is modified)
handler.write_ccc_file(enabled_plugins)
print("CC content repositioned alphabetically!")

# Restore a mod (backup preserved)
if handler.restore_mod_ba2("MyHeavyMod", "main"):
    print("Main BA2 restored! Backup still exists.")

# Check logs
logs = handler.get_log_entries(50)
for entry in logs[-10:]:  # Last 10 entries
    print(entry)
```

## BA2 Merging (v2.0+)

### `merge_cc_ba2s(fo4_path: str, output_name: str = "CCMerged") -> Dict[str, Any]`

Merge all Creation Club BA2 files into two unified archives to dramatically reduce BA2 count.

**Process:**
1. Backs up all CC BA2 files to timestamped folder
2. Extracts all CC BA2s (General and Texture separately)
3. **Automatic deduplication**: Files with same paths overwrite (last loaded wins)
4. Repacks into optimized archives:
   - `<output_name> - Main.ba2` (Format: General)
   - `<output_name> - Textures.ba2` or `Textures1.ba2`, `Textures2.ba2`, etc. (Format: DDS)
   - **Automatic 4GB splitting**: If textures exceed ~3.8GB, they're split into multiple archives
5. Creates dummy ESL file to load merged archives
6. Deletes original individual CC BA2 files

**Parameters:**
- `fo4_path` (str): Path to Fallout 4 installation
- `output_name` (str, optional): Base name for merged archives (default: "CCMerged")

**Returns:**

```python
{
    "success": True,
    "merged_main": "C:\\FO4\\Data\\CCMerged - Main.ba2",
    "merged_textures": [
        "C:\\FO4\\Data\\CCMerged - Textures1.ba2",
        "C:\\FO4\\Data\\CCMerged - Textures2.ba2"
    ],
    "texture_archive_count": 2,
    "dummy_esl": "C:\\FO4\\Data\\CCMerged.esl",
    "original_count": 338,
    "backup_path": "C:\\MO2\\BA2_Manager_Backups\\CC_Merge_Backup\\20251124_140530"
}
```

**Important Notes:**
- Duplicate files across CC BA2s are automatically deduplicated
- File overwrites follow alphabetical load order for CC content (sorted before extraction)
- Space savings typically 5-40% due to compression optimization and deduplication
- **Automatic 4GB limit**: Texture archives are automatically split to prevent memory issues
- Each archive stays under 4GB to ensure compatibility with all systems
- Operation can take 5-15 minutes depending on CC content installed

**Example:**

```python
result = handler.merge_cc_ba2s("C:\\Fallout4")
if result["success"]:
    print(f"Merged {result['original_count']} BA2s into 2 archives!")
    print(f"Backup: {result['backup_path']}")
```

### `restore_cc_ba2s(backup_path: str, fo4_path: str) -> Dict[str, Any]`

Restore original individual CC BA2 files from backup and remove merged archives.

**Parameters:**
- `backup_path` (str): Path to backup folder (from merge operation)
- `fo4_path` (str): Path to Fallout 4 installation

**Returns:**

```python
{
    "success": True,
    "restored_count": 169,
    "removed_merged": ["CCMerged - Main.ba2", "CCMerged - Textures.ba2", "CCMerged.esl"]
}
```

**Example:**

```python
# Find most recent backup
status = handler.get_cc_merge_status("C:\\Fallout4")
if status["available_backups"]:
    backup_path = status["available_backups"][0]["path"]
    result = handler.restore_cc_ba2s(backup_path, "C:\\Fallout4")
    print(f"Restored {result['restored_count']} original BA2s!")
```

### `get_cc_merge_status(fo4_path: str) -> Dict[str, Any]`

Check current merge status and available backups.

**Returns:**

```python
{
    "is_merged": True,
    "merged_files": ["CCMerged - Main.ba2", "CCMerged - Textures.ba2", "CCMerged.esl"],
    "individual_cc_count": 0,
    "available_backups": [
        {
            "path": "C:\\MO2\\BA2_Manager_Backups\\CC_Merge_Backup\\20251124_140530",
            "name": "20251124_140530",
            "cc_count": 169
        }
    ]
}
```

**Example:**

```python
status = handler.get_cc_merge_status("C:\\Fallout4")
if status["is_merged"]:
    print("CC BA2s are currently merged")
    print(f"Merged files: {status['merged_files']}")
else:
    print(f"Found {status['individual_cc_count']} individual CC BA2s")
```

---

### `merge_custom_ba2s(mod_names: list, fo4_path: str, output_name: str) -> Dict[str, Any]`

Merge specified mods' BA2 files into unified archives. Works with any list of mod names.

**Process:**
1. Finds all BA2 files for specified mods
2. Backs up all BA2 files to timestamped folder
3. **Sorts by modlist.txt load order** to maintain proper overwrite priority
4. Extracts all BA2s (Main and Texture separately) in load order
5. **Automatic deduplication**: Files with same paths overwrite (respects modlist.txt order)
6. Repacks into optimized archives with automatic 4GB splitting
7. Creates dummy ESL file to load merged archives
8. Deletes original individual BA2 files

**Parameters:**
- `mod_names` (list): List of mod names to merge (e.g., ["missweldy", "vchgs001fo4_ncrbeasthunter"])
- `fo4_path` (str): Path to Fallout 4 installation
- `output_name` (str): Base name for merged archives (e.g., "CustomMerged")

**Returns:**

```python
{
    "success": True,
    "merged_main": "C:\\FO4\\Data\\CustomMerged - Main.ba2",
    "merged_textures": [
        "C:\\FO4\\Data\\CustomMerged - Textures1.ba2"
    ],
    "texture_archive_count": 1,
    "dummy_esl": "C:\\FO4\\Data\\CustomMerged.esl",
    "mod_count": 2,
    "archive_count": 4,
    "backup_path": "C:\\MO2\\BA2_Manager_Backups\\Custom_Merge_Backup\\CustomMerged_20251124_153042"
}
```

**Important Notes:**
- **Respects modlist.txt load order**: Mods loaded later overwrite earlier mods (same as game behavior)
- Duplicate files across different mods are automatically deduplicated based on load order
- Automatic 4GB splitting for large texture archives
- Each archive stays under 4GB to ensure compatibility
- Space savings vary based on content overlap
- Operation time depends on number and size of BA2s being merged

**Example:**

```python
# Merge two armor mods
result = handler.merge_custom_ba2s(
    mod_names=["missweldy", "vchgs001fo4_ncrbeasthunter"],
    fo4_path="C:\\Fallout4",
    output_name="ArmorPack"
)

if result["success"]:
    print(f"Merged {result['mod_count']} mods ({result['archive_count']} BA2s)")
    print(f"Created: {result['merged_main']}")
    if result['texture_archive_count'] > 1:
        print(f"Note: Textures split into {result['texture_archive_count']} archives")
```
```

## Version Information

- **BA2 Manager Pro**: v2.0.0
- **Python**: 3.12+
- **PyQt6**: 6.10.0+
- **PyInstaller**: 6.16.0+

## See Also

- **README.md**: Feature overview and installation
- **QUICK_START.md**: Step-by-step user guide
- **CHANGELOG.md**: Version history
- **ba2_manager/gui/main_window.py**: GUI implementation examples
