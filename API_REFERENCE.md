# BA2 Manager - API Reference

## BA2Handler Class

Complete reference for the core BA2 operations handler.

### Initialization

```python
from ba2_manager.core.ba2_handler import BA2Handler

handler = BA2Handler(
    archive2_path="C:\\Path\\To\\Archive2.exe",  # Optional
    mo2_dir="C:\\MO2\\mods",                     # Optional, default: "mods"
    log_file="BA2_Extract.log"                   # Optional
)
```

### Methods

#### `count_ba2_files(fo4_path: str) -> Dict`
Count all BA2 files in the installation.

**Parameters:**
- `fo4_path` (str): Path to Fallout 4 installation

**Returns:**
```python
{
    "vanilla": 10,           # Base game BA2 count
    "mods": 42,              # Mod BA2 count
    "creation_club": 8,      # CC BA2 count
    "total": 60,             # Total count
    "limit": 255             # BA2 limit
}
```

**Example:**
```python
counts = handler.count_ba2_files("C:\\Program Files\\Fallout4")
print(f"Total: {counts['total']}/255")
```

---

#### `list_ba2_mods() -> List[BA2Info]`
List all BA2 mod files in MO2 directory.

**Returns:**
List of `BA2Info` dataclass objects with:
- `path`: Full file path
- `size`: File size in bytes
- `mod_name`: Parent mod name
- `is_extracted`: Boolean extraction status
- `file_count`: Number of files in archive

**Example:**
```python
mods = handler.list_ba2_mods()
for mod in mods:
    print(f"{mod.mod_name}: {mod.size / 1024 / 1024:.1f} MB")
```

---

#### `extract_ba2_file(ba2_path: str, output_dir: str = None) -> bool`
Extract a BA2 archive using Archive2.exe.

**Parameters:**
- `ba2_path` (str): Path to BA2 file to extract
- `output_dir` (str, optional): Output directory (defaults to BA2 location)

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = handler.extract_ba2_file(
    "C:\\MO2\\mods\\MyMod\\archive.ba2",
    "C:\\MO2\\mods\\MyMod\\extracted"
)

if success:
    print("Extraction complete!")
else:
    print("Extraction failed. Check logs.")
```

---

#### `repack_ba2_file(source_dir: str, output_ba2: str) -> bool`
Repack loose files into a BA2 archive.

**Parameters:**
- `source_dir` (str): Directory containing loose files
- `output_ba2` (str): Output BA2 file path

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = handler.repack_ba2_file(
    "C:\\extracted_files",
    "C:\\MO2\\mods\\MyMod\\archive.ba2"
)
```

---

#### `enable_cc_content(plugin_base: str) -> bool`
Enable Creation Club content.

**Parameters:**
- `plugin_base` (str): CC plugin base name (without extension)

**Returns:**
- `bool`: True if successful

**Example:**
```python
handler.enable_cc_content("ccbgsfo4001")
```

---

#### `disable_cc_content(plugin_base: str) -> bool`
Disable Creation Club content.

**Parameters:**
- `plugin_base` (str): CC plugin base name (without extension)

**Returns:**
- `bool`: True if successful

**Example:**
```python
handler.disable_cc_content("ccbgsfo4001")
```

---

#### `get_log_entries(lines: int = 50) -> str`
Retrieve recent log entries.

**Parameters:**
- `lines` (int): Number of lines to retrieve (default: 50)

**Returns:**
- `str`: Log content as text

**Example:**
```python
logs = handler.get_log_entries(100)
print(logs)
```

---

## Config Class

Configuration management for persistent settings.

### Initialization

```python
from ba2_manager.config import Config

config = Config()  # Uses default file: ba2_manager_config.json
# Or:
config = Config("custom_config.json")
```

### Methods

#### `load_config() -> Dict[str, Any]`
Load configuration from file (called automatically on init).

**Example:**
```python
config = Config()
settings = config.load_config()
```

---

#### `save_config(config: Dict = None)`
Save configuration to file.

**Parameters:**
- `config` (dict, optional): Config dict to save (saves current if None)

**Example:**
```python
config.config["archive2_path"] = "C:\\Path\\To\\Archive2.exe"
config.save_config()
```

---

#### `get(key: str, default: Any = None) -> Any`
Get a configuration value.

**Parameters:**
- `key` (str): Configuration key
- `default` (any): Default if key not found

**Returns:**
- Configuration value or default

**Example:**
```python
archive2 = config.get("archive2_path", "")
```

---

#### `set(key: str, value: Any)`
Set a configuration value and save.

**Parameters:**
- `key` (str): Configuration key
- `value` (any): Value to set

**Example:**
```python
config.set("fo4_path", "C:\\Program Files\\Fallout4")
```

---

#### `update(values: Dict[str, Any])`
Update multiple configuration values.

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

---

## BA2Info Dataclass

Information about a BA2 file.

**Fields:**
```python
@dataclass
class BA2Info:
    path: str           # Full file path
    size: int           # File size in bytes
    mod_name: str       # Parent mod name
    is_extracted: bool  # Extraction status (default: False)
    file_count: int     # Files in archive (default: 0)
```

**Example:**
```python
from ba2_manager.core.ba2_handler import BA2Info

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

## Constants

### VANILLA_BA2S
List of base game BA2 files.

```python
handler.VANILLA_BA2S = [
    "Fallout4.ba2",
    "Fallout4 - Textures.ba2",
    "DLCRobot.ba2",
    "DLCRobot - Textures.ba2",
    # ... (10 total)
]
```

### CC_NAMES
Dictionary mapping CC plugin IDs to names and BA2 counts.

```python
handler.CC_NAMES = {
    "ccacxfo4001": {"name": "Vault Suit Customization", "ba2_count": 2},
    "ccawnfo4001": {"name": "Graphic T-Shirt Pack", "ba2_count": 2},
    # ... (100+ entries)
}
```

---

## Error Handling

All methods include comprehensive error handling:

```python
handler = BA2Handler()

try:
    success = handler.extract_ba2_file("path/to/archive.ba2")
except FileNotFoundError:
    print("Archive2.exe or BA2 file not found")
except Exception as e:
    print(f"Extraction error: {e}")
    
    # Check failed extractions
    if handler.failed_extractions:
        print(f"Failed: {handler.failed_extractions}")
```

---

## Logging

All operations are logged to file:

```python
# Logs go to BA2_Extract.log (or configured path)
# Format: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE

# View logs programmatically
logs = handler.get_log_entries(50)
print(logs)
```

---

## Default Configuration

**File**: `ba2_manager_config.json`

```json
{
  "archive2_path": "",
  "mo2_mods_dir": "./mods",
  "fo4_path": "",
  "log_file": "BA2_Extract.log",
  "backup_dir": "./mod_backups"
}
```

---

## Complete Example

```python
from ba2_manager.core.ba2_handler import BA2Handler
from ba2_manager.config import Config

# Setup
config = Config()
handler = BA2Handler(
    archive2_path=config.get("archive2_path"),
    mo2_dir=config.get("mo2_mods_dir")
)

# Count BA2s
fo4_path = config.get("fo4_path")
if fo4_path:
    counts = handler.count_ba2_files(fo4_path)
    print(f"BA2 Count: {counts['total']}/255")
    
    if counts['total'] > 255:
        print("WARNING: Over BA2 limit!")
        
        # List mods
        mods = handler.list_ba2_mods()
        for mod in mods:
            print(f"  - {mod.mod_name}: {mod.size / 1024 / 1024:.1f} MB")
        
        # Extract one
        if mods:
            print(f"Extracting {mods[0].mod_name}...")
            if handler.extract_ba2_file(mods[0].path):
                print("Success!")
                logs = handler.get_log_entries()
                print(logs)
```

---

## Version Information

- **BA2 Manager**: 0.1.0
- **API Version**: 1.0
- **Python**: 3.12+
- **PyQt6**: 6.6.0+

---

*For GUI examples, see ba2_manager/gui/main_window.py*  
*For tests, see tests/test_ba2_handler.py*
