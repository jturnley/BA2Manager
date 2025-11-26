# BA2 Manager Pro v2.0.0-beta.5 - TESTING VERSION

**⚠️ BETA VERSION - FOR TESTING ONLY**

This version disables the 4GB splitting feature to test if split archives are causing texture loading issues.

## 🔧 Changes in Beta.5

### **4GB Splitting DISABLED for Testing**

The automatic 4GB splitting feature has been **completely disabled** in this version to isolate whether the splitting is causing texture loading problems.

**What this means:**
- All texture files are packed into a **single** `CCMerged - Textures.ba2` file
- No more `Textures1.ba2`, `Textures2.ba2`, etc.
- File may be **very large** (7-8+ GB compressed)
- This is for **diagnostic purposes only**

### **MO2 Integration (from beta.4)**
- Merged BA2 files placed in MO2 mod folder (`mods\CCMerged\`)
- Automatically registered in `modlist.txt` and `plugins.txt`
- MO2 manages files through virtual file system

## 📋 Testing Instructions

**CRITICAL: This is a diagnostic build to test if splitting causes issues**

1. **Before Testing:**
   - If you have beta.4 installed, use "Restore CC BA2s" first
   - This will remove the split archives and restore originals

2. **Perform CC Merge:**
   - Navigate to "Merge CC BA2s" tab
   - Click "Merge CC BA2s" button
   - **EXPECT LONGER PROCESSING TIME** (single large archive takes longer to pack)
   - Wait for merge to complete (~10-20 minutes)

3. **Verify Files Created:**
   - Check `mods\CCMerged\` folder
   - Should contain:
     - `CCMerged - Main.ba2` (~270 MB)
     - `CCMerged - Textures.ba2` (7-8+ GB - **VERY LARGE**)
     - `CCMerged.esl`

4. **Test in Game:**
   - Close and reopen MO2
   - Verify "CCMerged" mod is active in left pane
   - Launch Fallout 4 through MO2
   - **CHECK IF TEXTURES LOAD CORRECTLY**
   - Look for CC content (vault suits, armor, weapons)
   - Note if pink/purple placeholders still appear

5. **Report Results:**
   - ✅ If textures work: Splitting was the problem
   - ❌ If textures still broken: Issue is elsewhere (we'll investigate further)

## ⚠️ Important Notes

- **LARGE FILE WARNING**: The single texture archive will be 7-8+ GB
- **SLOWER PROCESSING**: Packing one huge archive takes longer than multiple smaller ones
- **THIS IS TEMPORARY**: If this fixes textures, we'll improve splitting in the next version
- **DO NOT USE FOR PRODUCTION**: This is a diagnostic build only

## 🔄 Version History

**Beta.5 (Current):**
- Disabled 4GB splitting to test texture loading
- Creates single large texture BA2 instead of multiple files

**Beta.4:**
- Added MO2 mod folder integration
- Automatic registration in modlist.txt and plugins.txt
- Fixed BA2 placement (was in Data folder, now in mods folder)

**Beta.3:**
- Debug logging enabled by default
- Added diagnostic tools
- Changed 4GB threshold to 7GB (3.5GB compressed target)

**Beta.2:**
- Fixed texture detection singular/plural

**Beta.1:**
- Initial CC merge system
- Custom mod merging
- 4GB automatic splitting (now disabled in beta.5)
- Load order preservation

## 📝 Version Info

- Version: 2.0.0-beta.5
- Build Date: November 25, 2025
- Python: 3.12.9
- PyQt6: 6.10.0
- PyInstaller: 6.16.0
- **4GB Splitting: DISABLED**

---

**Testing Goal:**
Determine if the 4GB splitting feature is causing texture loading issues. If single archive works, we know the problem is in the splitting logic.

Thank you for helping diagnose this issue! 🔍
