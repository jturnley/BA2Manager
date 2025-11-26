# BA2 Manager - Diagnostic Logging Guide

This guide explains the comprehensive diagnostic logging added in v2.0.0-beta.3 to help troubleshoot merge operations.

## Debug Mode

**Beta.3 Default**: Debug logging is **enabled by default** in all beta builds.

- Checkbox is checked by default in the GUI
- Provides detailed information about every step of the merge process
- Can be disabled if you only want basic progress messages
- Debug logs include timing, file counts, and detailed statistics

---

## CC Merge Diagnostics

### 1. Pre-Merge Information

Shows what's being merged before starting:

```
Starting CC BA2 merge process...
============================================================
Found 338 CC BA2 files to merge (sorted by load order)
DEBUG: Total original size: 1234.56 MB
DEBUG: First 10 BA2s by load order:
  1. ccBGSFO4001-PipBoy.ba2 (12.45 MB)
  2. ccBGSFO4003-PipBoy.ba2 (8.23 MB)
  3. ccBGSFO4006-PipBoy.ba2 (15.67 MB)
  ...
  ... and 328 more
```

**What this tells you:**
- Total number of CC BA2s found
- Combined size before merging
- Load order verification (CC content uses alphabetical order)
- File size distribution

### 2. Extraction Progress

Shows detailed extraction information for each BA2:

```
[1/338] Extracting ccBGSFO4001-PipBoy.ba2 to General/...
DEBUG:   Extracted 145 new files, 0 overwrites in 2.3s
[2/338] Extracting ccBGSFO4003-PipBoy.ba2 to General/...
DEBUG:   Extracted 98 new files, 12 overwrites in 1.8s
[3/338] Extracting ccBGSFO4001-PipBoy - Textures.ba2 to Textures/...
DEBUG:   Extracted 567 new files, 3 overwrites in 8.4s
```

**What this tells you:**
- Progress counter (X/Y)
- Which folder each BA2 extracts to (General vs Textures)
- How many new files vs overwrites
- Extraction time per archive
- Growing total file count

**Debugging value:**
- Slow extractions indicate large archives
- High overwrite counts show duplicate files being deduplicated
- Helps identify problematic archives

### 3. Deduplication Analysis

After extraction, shows which files appeared in multiple BA2s:

```
Extracted 210 general and 128 texture BA2s
Total unique files: 45123 general, 67890 textures

DEBUG: Deduplication: 234 files appeared in multiple BA2s
DEBUG: Most overwritten files:
  textures/armor/powerarmor/paint01_d.dds: in 5 BA2s (winner: ccXYZ...)
  meshes/weapons/pistol/barrel01.nif: in 3 BA2s (winner: ccABC...)
  materials/default.bgsm: in 8 BA2s (winner: ccDEF...)
```

**What this tells you:**
- How many unique files after deduplication
- Which files were duplicated across BA2s
- Which BA2 "won" each conflict (last in load order)
- Effectiveness of deduplication

**Debugging value:**
- High duplication = more space savings
- Shows which mods share resources
- Verifies load order priority is working correctly

### 4. Main Archive Packing

Shows compression statistics for non-texture files:

```
Creating merged main BA2: CCMerged - Main.ba2
Packing 45123 files, 2345.67 MB uncompressed
Created CCMerged - Main.ba2 in 45.2s
  Final: 1234.56 MB, 45123 files
  Compression: 2345.67 MB → 1234.56 MB (47.3%)
  Original 210 BA2s: 1456.78 MB
  Space saved: 222.22 MB (15.3%)
```

**What this tells you:**
- How many files are being packed
- Uncompressed size before BA2 compression
- Final compressed size
- Compression ratio achieved
- Time taken to pack
- Space savings vs original BA2s

**Debugging value:**
- Low compression = mostly non-compressible files (meshes, etc.)
- High compression = text/XML files
- Pack time indicates system performance
- Space savings shows merge effectiveness

### 5. Texture Archive Packing

Shows detailed splitting and compression for DDS textures:

```
Total uncompressed texture data: 13.45GB
Using 7.0GB uncompressed threshold (targets ~3.5GB compressed)
Splitting 67890 texture files into 2 archives

Creating CCMerged - Textures1.ba2 with 37451 files (6.89GB uncompressed)...
DEBUG:   Sample texture paths: [
    'textures/actors/character/basehumanfemale_d.dds',
    'textures/armor/powerarmor/t51_torso_d.dds',
    'textures/weapons/pistol10mm/receiver_d.dds'
  ]
  Created CCMerged - Textures1.ba2 in 125.3s: 3421.45 MB (50.2% compression)
    Compression: 6.89 GB → 3421.45 MB (50.2%)

Creating CCMerged - Textures2.ba2 with 30439 files (6.56GB uncompressed)...
  Created CCMerged - Textures2.ba2 in 118.7s: 3287.23 MB (50.8% compression)
    Compression: 6.56 GB → 3287.23 MB (50.8%)
```

**What this tells you:**
- Total uncompressed texture data
- 4GB splitting threshold (7GB uncompressed → ~3.5GB compressed)
- Number of archives created
- Files per archive
- Sample paths (verify correct files are included)
- Compression ratio per archive (~50% for DDS)
- Pack time per archive

**Debugging value:**
- Verifies 4GB splitting is working (should get ~3.5GB archives)
- Shows DDS compression effectiveness (~50% typical)
- Sample paths help verify texture files are correct
- Multiple small archives = need higher threshold
- Single huge archive = need lower threshold

### 6. Final Summary

Comprehensive statistics at end of merge:

```
============================================================
CC BA2 MERGE SUMMARY:
  Original: 338 CC BA2 files
  Merged: 3 BA2 file(s)
  Reduction: 338 → 3 (99.1% fewer files)
  Total space: 2567.89 MB → 2345.67 MB
  Space saved: 222.22 MB (8.7%)
  Backup: C:\...\CC_Merge_Backup\20251125_091823
============================================================
CC BA2 merge completed successfully!
```

**What this tells you:**
- Original BA2 count
- Final BA2 count
- File reduction percentage
- Total space before and after
- Total space saved
- Backup location (for restore if needed)

---

## Custom Mod Merge Diagnostics

### 1. Pre-Merge Information

Shows selected mods and their BA2s:

```
Starting custom mod merge: MyModPack
============================================================
Merging 15 BA2 files from 5 mods

DEBUG: Selected mods:
  1. ArmorMod (3 BA2s, 234.56 MB)
  2. WeaponMod (4 BA2s, 456.78 MB)
  3. TexturePack (2 BA2s, 890.12 MB)
  4. MiscItems (4 BA2s, 123.45 MB)
  5. EnvironmentalFX (2 BA2s, 345.67 MB)

Sorted 15 BA2s by modlist.txt load order
DEBUG: Load order (first 10):
  1. ArmorMod - Main.ba2 (123.45 MB)
  2. ArmorMod - Textures.ba2 (111.11 MB)
  3. WeaponMod - Main.ba2 (234.56 MB)
  ...
  ... and 5 more
```

**What this tells you:**
- Which mods are being merged
- BA2 count per mod
- Size per mod
- Final load order from modlist.txt
- Verifies correct load order priority

**Debugging value:**
- Confirms selected mods are correct
- Shows if any mods are missing BA2s
- Verifies load order matches MO2

### 2. Extraction Progress

Similar to CC merge but with load order emphasis:

```
[1/8] Extracting ArmorMod - Main.ba2 (load order maintained)...
DEBUG:   Extracted 1234 files in 12.3s (total now: 1234)
[2/8] Extracting WeaponMod - Main.ba2 (load order maintained)...
DEBUG:   Extracted 567 files in 5.6s (total now: 1801)
...

[1/7] Extracting ArmorMod - Textures.ba2...
DEBUG:   Extracted 3456 files in 34.5s (total now: 3456)
[2/7] Extracting WeaponMod - Textures.ba2...
DEBUG:   Extracted 2345 files in 23.4s (total now: 5801)
```

**What this tells you:**
- Progress through main and texture archives separately
- Running total file count
- Extraction time per archive
- Load order is maintained

### 3. Packing Statistics

Same detailed compression info as CC merge:

```
Creating MyModPack - Main.ba2 (5801 files, 1234.56 MB uncompressed)...
  Created in 23.4s: 678.90 MB (45.0% compression)

Total uncompressed texture data: 8.45GB
Using 7.0GB uncompressed threshold (targets ~3.5GB compressed)
Splitting 12345 texture files into 2 archives

Creating MyModPack - Textures1.ba2 with 6789 files (6.23GB uncompressed)...
  Created MyModPack - Textures1.ba2 in 89.4s: 3123.45 MB (49.8% compression)
Creating MyModPack - Textures2.ba2 with 5556 files (2.22GB uncompressed)...
  Created MyModPack - Textures2.ba2 in 34.2s: 1112.34 MB (50.1% compression)
```

### 4. Final Summary

```
============================================================
CUSTOM MERGE SUMMARY: MyModPack
  Source: 5 mods, 15 BA2 files
  Merged: 3 BA2 file(s)
  Reduction: 15 → 3 (80.0% fewer files)
  Total space: 2050.58 MB → 1914.69 MB
  Space saved: 135.89 MB (6.6%)
  Backup: C:\...\Custom_Merge_Backup\MyModPack_20251125_091823
============================================================
Custom merge completed: MyModPack
```

---

## What to Report When Issues Occur

### For Texture Errors:
Include from log:
1. Extraction messages showing which BA2s extracted to Textures/
2. Sample texture paths shown during packing
3. Final compression ratios (should be ~50%)
4. Any Archive2.exe error messages

### For Missing Content:
Include from log:
1. Load order listing (first 10 entries)
2. Deduplication statistics
3. Which BA2 "won" for conflicting files
4. Final file counts (general/textures)

### For Wrong Archive Sizes:
Include from log:
1. "Total uncompressed texture data" line
2. "Using X.XGB uncompressed threshold" line
3. All "Creating" lines with uncompressed and compressed sizes
4. Final summary with space statistics

### For Performance Issues:
Include from log:
1. Extraction times per BA2
2. Pack times per archive
3. Total file counts
4. System specs (CPU, RAM, disk type)

---

## Performance Benchmarks

Typical times for reference:

- **Extraction**: 1-10 seconds per BA2 (depends on file count)
- **Main packing**: 30-120 seconds (depends on file count)
- **Texture packing**: 60-300 seconds per archive (depends on size)
- **Full CC merge (338 BA2s)**: 10-20 minutes total

Slow operations usually indicate:
- Large file counts (>10,000 files)
- Slow disk I/O (HDD vs SSD)
- High system load
- Many large texture files

---

## Log File Location

Logs are saved to:
- **Console**: Shows INFO level and above
- **File**: `ba2-manager.log` (shows DEBUG level when enabled)

Look for the log file in:
- Same folder as `ba2-manager.exe`
- Or in your configured working directory

The log file persists between runs and shows the complete history of operations.

---

## Built-in Diagnostic Tools (v2.0.0-beta.3+)

BA2 Manager now includes two convenient buttons in the Settings tab:

### Enable Fallout 4 Debug Logging

Click this button to automatically configure Fallout 4 for debug logging:

**What it does:**
- Modifies `Documents\My Games\Fallout4\Fallout4Custom.ini`
- Adds Papyrus script logging settings
- Enables trace and debug information
- Creates `Logs\Script\` directory if needed
- Shows exactly where logs will be saved

**Settings added:**
```ini
[Papyrus]
bEnableLogging=1
bEnableTrace=1
bLoadDebugInformation=1

[Archive]
bInvalidateOlderFiles=1
sResourceDataDirsFinal=
```

**After enabling:**
- Restart Fallout 4 for changes to take effect
- Logs will appear in `Documents\My Games\Fallout4\Logs\Script\`
- Useful for diagnosing script errors and mod conflicts

### Bundle All Logs to ZIP

Click this button to collect all logs into a single zip file:

**What it includes:**
- `ba2-manager.log` (BA2 Manager's log)
- MO2 logs (from `MO2\logs\*.log` and `*.txt`)
- Fallout 4 Papyrus logs (script logs)
- F4SE logs (if F4SE is installed)
- Crash logs (if any exist)

**Output:**
- Creates `BA2_Manager_Logs_YYYYMMDD_HHMMSS.zip` in your MO2 folder
- Shows summary of all files included
- Perfect for sharing when reporting bugs

**Use this when:**
- Reporting bugs or issues
- Asking for help with merge problems
- Documenting problems for troubleshooting
- Providing complete diagnostic information
