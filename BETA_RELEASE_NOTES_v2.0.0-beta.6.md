# BA2 Manager Pro v2.0.0-beta.6 - FIXED BUILD

**⚠️ BETA VERSION - FOR TESTING ONLY**

This version fixes the backup status detection that was broken in beta.4/5.

## 🔧 Changes in Beta.6

### **Fixed: Backup Status Detection**

The "Merge CC BA2s" tab status page was broken and couldn't detect:
- Whether CC BA2s were already merged
- What merged files exist
- Available backup folders

**Root Cause:**
The code was looking for merged files in `Fallout4\Data\` folder (old location), but beta.4 changed the merge to create files in `mods\CCMerged\` folder (new MO2 mod location).

**The Fix:**
- `get_cc_merge_status()` now checks the MO2 mod folder (`mods\CCMerged\`) for merged files
- Old code preserved in comments in case we need to revert to Fallout4.ini method
- Status page now correctly shows:
  - ✓ If merge exists
  - List of merged files
  - Available backups for restore
  - Enables/disables Merge and Restore buttons correctly

### **Still Included from Beta.5:**
- **4GB splitting DISABLED** (single large texture BA2 for testing)
- MO2 mod folder integration (from beta.4)
- Automatic registration in modlist.txt and plugins.txt

## 📋 Testing Instructions

1. **Open BA2 Manager:**
   - Navigate to "Merge CC BA2s" tab
   - Status should now correctly show:
     - If already merged: "✓ CC BA2s are currently MERGED"
     - Available backups with BA2 counts
     - Correct button states (Merge disabled if merged, Restore enabled if backup exists)

2. **If Status Shows Merged:**
   - "Restore" button should be enabled
   - Click to restore original CC BA2s
   - Verify it removes `mods\CCMerged\` folder
   - Verify it restores cc*.ba2 files to Data folder

3. **If Status Shows Not Merged:**
   - "Merge" button should be enabled
   - Can proceed with merge operation
   - After merge, status should update to show merged state

4. **Test Texture Loading:**
   - After merge, launch game through MO2
   - Check if CC content textures load correctly
   - Still testing if single large BA2 fixes texture issue

## 🔄 Version History

**Beta.6 (Current):**
- **FIXED**: Backup status detection looks in correct location (MO2 mod folder)
- Old code preserved in comments for potential Fallout4.ini fallback method
- Merge/Restore buttons now work correctly

**Beta.5:**
- Disabled 4GB splitting (creates single large texture BA2)

**Beta.4:**
- Changed merge output to MO2 mod folder
- Added automatic MO2 registration
- (Broke status detection - fixed in beta.6)

**Beta.3:**
- Debug logging enabled by default
- Changed 4GB threshold to 7GB

**Beta.2:**
- Fixed texture detection singular/plural

**Beta.1:**
- Initial CC merge system
- Original 4GB splitting (now disabled)

## ⚠️ Important Notes

- **4GB splitting still DISABLED** - Creates single large texture BA2
- **Old code preserved** - Commented out in case we need Fallout4.ini method
- Status page now works correctly with new file locations
- Merge/Restore functionality fully operational

## 📝 Version Info

- Version: 2.0.0-beta.6
- Build Date: November 25, 2025
- Python: 3.12.9
- PyQt6: 6.10.0
- PyInstaller: 6.16.0
- **4GB Splitting: DISABLED**
- **Status Detection: FIXED**

---

**What's Fixed:**
The UI now correctly detects merged state and enables/disables buttons appropriately. You can now see merge status and use the restore function properly.

**Still Testing:**
Whether single large texture BA2 (no splitting) fixes the texture loading issue.

Thank you for beta testing! 🙏
