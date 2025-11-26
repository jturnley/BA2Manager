# BA2 Manager Pro v2.0.0-beta.1 - BETA RELEASE

**⚠️ BETA VERSION - FOR TESTING ONLY**

This is a pre-release beta version for testing purposes. Please report any issues before final release.

## 🆕 Major New Features

### 1. **CC BA2 Merge System**
- One-click merge of all Creation Club BA2 files
- Automatically combines 300+ CC archives into 2-3 optimized files
- Creates dummy ESL for proper load order
- Full backup and restore functionality
- Typical space savings: 5-40% (370MB in testing)

### 2. **Custom Mod Merging**
- Merge any selection of regular mods together
- Checkbox selection in mod list
- Custom naming for merged archives
- Same optimization and splitting as CC merge

### 3. **4GB Automatic Splitting**
- Large texture archives automatically split at 3.8GB threshold
- Prevents memory issues on resource-constrained systems
- Uses smart bin-packing algorithm (largest-first)
- Multiple output archives: Textures1.ba2, Textures2.ba2, etc.

### 4. **Load Order Preservation**
- **CRITICAL FIX**: Now respects modlist.txt load order
- CC content sorted alphabetically (correct for CC)
- Regular mods sorted by MO2 priority
- File overwrites match game behavior exactly

## 🔧 Technical Improvements

### Deduplication
- Automatic deduplication during merge
- Files with identical paths are merged (last in load order wins)
- Significantly reduces final archive size

### ESL Format
- Fixed ESL structure to 49 bytes (TES4 + HEDR + CNAM)
- MO2 parses without errors
- Proper record and subrecord sizes

### Archive Processing
- Archive2.exe integration with extended timeouts (300-600s)
- Robust error handling and logging
- Progress feedback during operations

## 📋 What to Test

### Critical Test Cases:
1. **CC Merge**:
   - Navigate to "Merge CC BA2s" tab
   - Click "Merge CC BA2s" button
   - Verify: MO2 loads without ESL errors
   - Verify: Game loads and CC content works
   - Test restore function

2. **Custom Mod Merge**:
   - Go to "Manage BA2s" tab
   - Check "Merge" checkbox for 2-3 mods
   - Enter custom name (e.g., "TestMerge")
   - Verify: Archives created in correct order
   - Verify: Game loads properly

3. **Load Order**:
   - Check that merged files respect your modlist.txt order
   - Files from mods with higher priority should win conflicts
   - Check MO2 log for any warnings

4. **4GB Splitting**:
   - If you have large texture archives (>4GB combined), verify splitting
   - Multiple Textures*.ba2 files should be created
   - Game should load all splits correctly

### Known Limitations:
- Merge operations can take 5-15 minutes depending on BA2 count
- No progress bar during extraction (planned for future)
- Custom merge restore not yet implemented (planned)
- Large operations may appear frozen (check log for activity)

## 🐛 Bug Reporting

Please report issues with:
- Your MO2 version
- Number of mods/BA2s involved
- Screenshots of errors
- Log file content (if applicable)
- Steps to reproduce

## 📦 Installation

1. Extract `BA2_Manager_v2.0.0-beta.1.zip`
2. Place `ba2-manager.exe` in your MO2 folder
3. Configure paths in Settings tab
4. Test on a BACKUP of your setup first!

## ⚠️ Important Notes

- **BACKUP YOUR SETUP** before testing merge features
- Merge creates automatic backups, but be safe
- Test on non-essential mods first
- CC merge has been tested successfully (338 → 3 files)
- Custom merge is new - needs testing!

## 🔄 Changes Since v1.1.4

- Added complete BA2 merging system (CC and custom)
- Fixed load order to respect modlist.txt
- Added 4GB automatic splitting
- Added backup/restore for CC merge
- **Fixed critical bug: BA2s in subdirectories now properly filtered by active mods**
- Updated API documentation
- Improved logging and error handling

## 📝 Version Info

- Version: 2.0.0-beta.1
- Build Date: November 24, 2025
- Python: 3.12.9
- PyQt6: 6.10.0
- PyInstaller: 6.16.0

---

**Next Steps:**
1. Test all features thoroughly
2. Report any issues or bugs
3. Provide feedback on usability
4. Final v2.0.0 release after testing phase

Thank you for beta testing! 🙏
