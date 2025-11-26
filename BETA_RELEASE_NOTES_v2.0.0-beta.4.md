# BA2 Manager Pro v2.0.0-beta.4 - BETA RELEASE

**⚠️ BETA VERSION - FOR TESTING ONLY**

This beta version fixes a critical issue with how merged CC BA2 files are loaded by the game.

## 🔧 Critical Fix in Beta.4

### **MO2 Mod Folder Integration**
Previously in beta.3, merged CC BA2 files were placed in `Portable\Data\` which bypassed MO2's virtual file system, causing the game to show pink/purple texture placeholders.

**Beta.4 changes:**
- Merged BA2 files are now placed in a proper MO2 mod folder (`mods\CCMerged\`)
- The mod is automatically registered in `modlist.txt` as active
- The dummy ESL is automatically registered in `plugins.txt` as active
- MO2 now properly manages the merged files through its virtual file system
- Game loads textures correctly through MO2's VFS

### **What This Fixes:**
- ✅ Pink/purple texture placeholders are now resolved
- ✅ Game properly loads merged CC content
- ✅ MO2 shows the merged mod in the left pane
- ✅ No manual INI editing required
- ✅ Merge can be easily disabled/enabled in MO2 like any other mod

### **Restore Function Updated:**
The restore function now:
- Removes the `CCMerged` mod folder from `mods\` directory
- Unregisters the mod from `modlist.txt`
- Unregisters the plugin from `plugins.txt`
- Restores original CC BA2s to game Data folder
- Deletes the backup folder

## 📋 Testing Instructions

1. **Perform CC Merge:**
   - Open BA2 Manager Pro
   - Navigate to "Merge CC BA2s" tab
   - Click "Merge CC BA2s" button
   - Wait for merge to complete (~5-15 minutes)

2. **Verify in MO2:**
   - Close and reopen MO2
   - Check left pane for "CCMerged" mod (should be active)
   - Check right pane for "CCMerged.esl" plugin (should be active)
   - Mod should be at Priority 0 (bottom of load order)

3. **Test in Game:**
   - Launch Fallout 4 through MO2
   - Verify CC content loads correctly
   - Check that textures appear properly (no pink/purple placeholders)
   - Test CC items, armor, weapons, etc.

4. **Test Restore:**
   - In BA2 Manager, click "Restore CC BA2s"
   - Verify original CC BA2s are restored
   - Check that "CCMerged" mod is removed from MO2
   - Verify plugins.txt no longer lists CCMerged.esl

## 🆕 All Beta Features (from beta.1-4)

### 1. **CC BA2 Merge System**
- One-click merge of all Creation Club BA2 files
- Automatically combines 300+ CC archives into 2-3 optimized files
- Creates dummy ESL for proper load order
- Full backup and restore functionality
- Typical space savings: 5-40% (370MB in testing)
- **NEW: Creates proper MO2 mod folder with auto-registration**

### 2. **Custom Mod Merging**
- Merge any selection of regular mods together
- Checkbox selection in mod list
- Custom naming for merged archives
- Same optimization and splitting as CC merge

### 3. **4GB Automatic Splitting**
- Large texture archives automatically split at 7GB uncompressed threshold
- Prevents memory issues on resource-constrained systems
- Uses smart bin-packing algorithm (largest-first)
- Multiple output archives: Textures1.ba2, Textures2.ba2, etc.
- Targets ~3.5GB per compressed archive

### 4. **Load Order Preservation**
- Respects modlist.txt load order
- CC content sorted alphabetically (correct for CC)
- Regular mods sorted by MO2 priority
- File overwrites match game behavior exactly

### 5. **Debug Logging & Diagnostics**
- Debug logging enabled by default
- FO4 debug logging enabler button
- Log bundler button (creates timestamped zip)
- Comprehensive merge statistics

## 🐛 Bug Fixes (Beta.1-4)

- ✅ Fixed: BA2s in subdirectories now properly filtered by active mods (beta.1)
- ✅ Fixed: Texture detection handles singular/plural "Texture/Textures" (beta.2)
- ✅ Fixed: 4GB splitting producing 2GB files (changed to 7GB threshold) (beta.3)
- ✅ Fixed: Debug logging verbosity (enabled by default) (beta.3)
- ✅ **CRITICAL FIX: Merged BA2s now load properly in-game via MO2 VFS (beta.4)**

## ⚠️ Important Notes

- **BACKUP YOUR SETUP** before testing merge features
- Merge creates automatic backups, but be safe
- Test on non-essential mods first
- CC merge has been tested successfully (338 → 3 files)
- **Beta.4 resolves the pink texture issue from beta.3**

## 📦 Installation

1. Extract `BA2_Manager_v2.0.0-beta.4.zip`
2. Place `ba2-manager.exe` in your MO2 folder
3. Configure paths in Settings tab
4. Test on a BACKUP of your setup first!

## 🔄 Changes Since Beta.3

- **CRITICAL**: Merged BA2 files now placed in MO2 mod folder instead of game Data folder
- Added automatic mod registration to modlist.txt and plugins.txt
- Updated restore function to remove mod folder and unregister from MO2 lists
- Fixed texture loading issue (pink/purple placeholders)

## 📝 Version Info

- Version: 2.0.0-beta.4
- Build Date: November 25, 2025
- Python: 3.12.9
- PyQt6: 6.10.0
- PyInstaller: 6.16.0

---

**Next Steps:**
1. Test CC merge with new MO2 integration
2. Verify textures load correctly in-game
3. Test restore functionality
4. Report any issues or bugs
5. Final v2.0.0 release after testing phase

Thank you for beta testing! 🙏
