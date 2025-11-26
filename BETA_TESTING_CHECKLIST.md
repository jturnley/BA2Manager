# BA2 Manager v2.0.0-beta.1 Testing Checklist

## Pre-Testing Setup
- [ ] Extract beta build to test location
- [ ] Configure MO2 paths in Settings tab
- [ ] **BACKUP your MO2 setup** (profiles folder at minimum)
- [ ] Note current BA2 count in Data folder

## Test 1: CC BA2 Merge
- [ ] Open "Merge CC BA2s" tab
- [ ] Verify CC BA2 count is displayed correctly
- [ ] Click "Merge CC BA2s" button
- [ ] Wait for completion (may take 5-15 minutes)
- [ ] Check results:
  - [ ] CCMerged - Main.ba2 created in Data folder
  - [ ] CCMerged - Textures*.ba2 created (may be multiple if >4GB)
  - [ ] CCMerged.esl created in Data folder
  - [ ] Original cc*.ba2 files removed
  - [ ] Backup created in BA2_Manager_Backups/CC_Merge_Backup/
- [ ] Launch MO2
  - [ ] No ESL parsing errors in log
  - [ ] CCMerged.esl appears in plugin list
- [ ] Launch game
  - [ ] Game loads successfully
  - [ ] CC content still works
  - [ ] No texture issues
- [ ] Test Restore
  - [ ] Click "Restore CC BA2s" button
  - [ ] Original cc*.ba2 files restored
  - [ ] Merged files removed

## Test 2: Custom Mod Merge (Light Test)
- [ ] Go to "Manage BA2s" tab
- [ ] Select 2-3 small/medium mods with "Merge" checkbox
- [ ] Note which mods are selected
- [ ] Enter custom name (e.g., "TestPack")
- [ ] Confirm merge
- [ ] Wait for completion
- [ ] Check results:
  - [ ] TestPack - Main.ba2 created
  - [ ] TestPack - Textures*.ba2 created (if applicable)
  - [ ] TestPack.esl created
  - [ ] Original mod BA2s removed
  - [ ] Backup created in BA2_Manager_Backups/Custom_Merge_Backup/
- [ ] Launch MO2
  - [ ] No ESL parsing errors
  - [ ] TestPack.esl in plugin list
- [ ] Launch game
  - [ ] Game loads
  - [ ] Merged mod content works

## Test 3: Load Order Verification
- [ ] Open MO2 log after merge
- [ ] Check for "Sorted by modlist.txt load order" message
- [ ] Verify no unexpected file conflicts
- [ ] If you have mods that modify same files:
  - [ ] Higher priority mod's changes should be visible
  - [ ] Lower priority mod's changes should be overwritten

## Test 4: 4GB Splitting (If Applicable)
- [ ] If you have large texture sets:
  - [ ] Multiple Textures*.ba2 files created
  - [ ] Each file under 4GB
  - [ ] All load correctly in game
- [ ] If total textures <4GB:
  - [ ] Single Textures.ba2 created

## Test 5: Error Handling
- [ ] Try merge with no mods selected → Should show error
- [ ] Try merge with Archive2.exe path wrong → Should show error
- [ ] Try restore with no backup → Should handle gracefully

## Issues Found

### Issue 1:
**Description:**
**Steps to Reproduce:**
**Expected:**
**Actual:**
**Severity:** (Critical/Major/Minor)

### Issue 2:
**Description:**
**Steps to Reproduce:**
**Expected:**
**Actual:**
**Severity:**

## Performance Notes
- Time taken for CC merge: ________ minutes
- Time taken for custom merge: ________ minutes
- Memory usage during merge: ________ (if noticeable)

## System Info
- MO2 Version: __________
- Number of CC BA2s: __________
- Number of total mods: __________
- Total BA2 count before: __________
- Windows Version: __________
- RAM: __________

## Overall Assessment
- [ ] All features work as expected
- [ ] Some issues found (see above)
- [ ] Critical issues found - do not release

## Additional Comments


---

**Return this completed checklist along with any logs/screenshots of issues found.**
