# BA2 Manager Pro v2.0.0-beta.3 - BETA RELEASE

**⚠️ BETA VERSION - FOR TESTING ONLY**

## 🔧 Changes in beta.3

### Fixed 4GB Archive Splitting
- **CRITICAL FIX**: Increased uncompressed threshold from 3.8GB to 7GB
- **Why**: DDS textures compress to ~50% in BA2 archives
- **Result**: You should now get ~3.5GB compressed archives instead of 2GB
- **Added logging**: Shows uncompressed size per archive group for verification

### Debug Logging Enabled by Default
- **NEW**: Debug mode is now **always enabled** in beta.3 for better diagnostics
- Checkbox is checked by default in the GUI
- Provides comprehensive logging for troubleshooting merge issues
- You can still disable it if desired

### Enhanced Diagnostic Logging
Added extensive debug information to help diagnose merge issues:

**Pre-Merge Diagnostics:**
- Total size of BA2s being merged
- Load order verification showing first 10 files
- Per-mod BA2 count and sizes (custom merge)

**During Extraction:**
- File count tracking with overwrites detected
- Extraction timing for each BA2
- Shows which files are being overwritten (deduplication)

**Post-Extraction Analysis:**
- Deduplication statistics
- Most overwritten files (shows which BA2 wins conflicts)
- Final unique file counts

**During Packing:**
- Uncompressed vs compressed sizes
- Compression ratios for each archive
- Pack timing for performance analysis
- Sample texture paths for debugging

**Summary Statistics:**
- File reduction percentages
- Space savings with before/after comparison
- Performance metrics (extraction/packing times)
- Backup location

### New Diagnostic Tools (Settings Tab)

**Enable Fallout 4 Debug Logging Button:**
- One-click setup of Fallout 4's debug logging
- Automatically modifies `Fallout4Custom.ini` with proper settings
- Enables Papyrus script logging for troubleshooting
- Creates log directories if they don't exist
- Shows exactly where logs will be saved

**Bundle All Logs to ZIP Button:**
- Collects all relevant logs in one click
- Includes: ba2-manager.log, MO2 logs, FO4 Papyrus logs, F4SE logs, crash logs
- Creates timestamped zip file in MO2 folder
- Perfect for bug reports and troubleshooting
- Shows summary of all files included

### The Problem in beta.1/beta.2:
The splitting algorithm was using **3.8GB of uncompressed files** as the limit, but after BA2 compression, this resulted in only ~2GB archives. Now we use **7GB uncompressed** which compresses down to ~3.5GB, much closer to the 4GB target.

### Example Logging Output:
```
============================================================
Starting CC BA2 merge process...
Found 338 CC BA2 files to merge (sorted by load order)
DEBUG: Total original size: 1234.56 MB
DEBUG: First 10 BA2s by load order:
  1. ccBGSFO4001-PipBoy.ba2 (12.45 MB)
  2. ccBGSFO4003-PipBoy.ba2 (8.23 MB)
  ...

[1/338] Extracting ccBGSFO4001-PipBoy.ba2 to General/...
DEBUG:   Extracted 145 new files, 0 overwrites in 2.3s
[2/338] Extracting ccBGSFO4003-PipBoy.ba2 to General/...
DEBUG:   Extracted 98 new files, 12 overwrites in 1.8s
...

Extracted 210 general and 128 texture BA2s
Total unique files: 45123 general, 67890 textures
DEBUG: Deduplication: 234 files appeared in multiple BA2s
DEBUG: Most overwritten files:
  textures/armor/powerarmor/paint01_d.dds: in 5 BA2s (winner: ccXYZ...)

Creating merged main BA2: CCMerged - Main.ba2
Packing 45123 files, 2345.67 MB uncompressed
Created CCMerged - Main.ba2 in 45.2s
  Final: 1234.56 MB, 45123 files
  Compression: 2345.67 MB → 1234.56 MB (47.3%)
  Original 210 BA2s: 1456.78 MB
  Space saved: 222.22 MB (15.3%)

Total uncompressed texture data: 13.45GB
Using 7.0GB uncompressed threshold (targets ~3.5GB compressed)
Splitting 67890 texture files into 2 archives
Creating CCMerged - Textures1.ba2 with 37451 files (6.89GB uncompressed)...
  Created CCMerged - Textures1.ba2 in 125.3s: 3421.45 MB (50.2% compression)
    Compression: 6.89 GB → 3421.45 MB (50.2%)
Creating CCMerged - Textures2.ba2 with 30439 files (6.56GB uncompressed)...
  Created CCMerged - Textures2.ba2 in 118.7s: 3287.23 MB (50.8% compression)
    Compression: 6.56 GB → 3287.23 MB (50.8%)

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

## 🐛 From Previous Betas

### beta.2 Changes:
- Fixed texture BA2 detection (singular/plural)
- Added extraction and path logging for texture debugging

### beta.1 Changes:
- Fixed subdirectory BA2 filtering bug
- CC merge system
- Custom mod merging
- Load order preservation

## 📦 Installation

1. Extract `BA2_Manager_v2.0.0-beta.3.zip`
2. Place `ba2-manager.exe` in your MO2 folder  
3. Configure paths in Settings tab
4. **BACKUP YOUR SETUP** before testing!

## 📊 What to Check

After merging, verify in your log:
- `Total uncompressed texture data:` shows your total texture size
- Each archive should show **uncompressed size** (6-7GB) and **compressed size** (~3.5GB)
- Final archives should be closer to 4GB than 2GB

If you still get 2GB archives, please send the log showing the "Creating" lines with both sizes!

## 📝 Version Info

- Version: 2.0.0-beta.3
- Build Date: November 25, 2025  
- Python: 3.12.9
- PyQt6: 6.10.0

---

**This beta fixes the 4GB splitting to actually produce ~4GB archives instead of ~2GB!**
