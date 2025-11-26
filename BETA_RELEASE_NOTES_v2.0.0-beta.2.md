# BA2 Manager Pro v2.0.0-beta.2 - BETA RELEASE

**⚠️ BETA VERSION - FOR TESTING ONLY**

This is beta.2 with texture debugging improvements and fixes.

## 🔧 Changes in beta.2

### Texture Debugging & Fixes
- **Fixed texture BA2 detection**: Now properly detects both `" - texture"` and `" - textures"` (singular/plural)
- **Added extraction logging**: Shows which folder (General/ or Textures/) each BA2 is extracted to
- **Added path structure logging**: Shows sample file paths being packed into texture archives
- **Improved Archive2.exe output logging**: Captures and logs extraction output for debugging

### Bug Fixes from beta.1
- Fixed critical bug: BA2s in subdirectories now properly filtered by active mods
- Improved texture path handling during merge

## 📋 If You're Experiencing Texture Issues

Please test with this beta.2 build and provide:

1. **Log file**: Send the full `ba2-manager.log` file after merge
2. **Which items**: Specific CC items showing texture problems
3. **What you see**: Pink/purple textures? Black textures? Missing entirely?
4. **Sample paths**: The log will now show "Sample texture paths:" - please include these lines

Look for these lines in your log:
```
Extracting <ba2-name> to Textures/...
Sample texture paths: ['textures/...', ...]
```

This will help diagnose if the issue is:
- Wrong archive format (General vs DDS)
- Wrong internal path structure
- Missing texture files
- Extraction problems

## 🆕 Major Features (from v1.1.4)

- CC BA2 merge system (one-click merge of 300+ CC archives)
- Custom mod merging (select any mods to merge)
- 4GB automatic splitting (prevents memory issues)
- Load order preservation (respects modlist.txt)
- Automatic deduplication
- Full backup and restore

## 📦 Installation

1. Extract `BA2_Manager_v2.0.0-beta.2.zip`
2. Place `ba2-manager.exe` in your MO2 folder
3. Configure paths in Settings tab
4. **BACKUP YOUR SETUP** before testing!

## 🐛 Reporting Texture Issues

When reporting texture problems, include:
- Full ba2-manager.log file (critical for debugging!)
- Screenshots of affected items in-game
- List of specific CC content with problems
- Whether restore fixes the issue

## 📝 Version Info

- Version: 2.0.0-beta.2
- Build Date: November 25, 2025
- Python: 3.12.9
- PyQt6: 6.10.0

---

**This beta specifically addresses texture issues - please test and report!**
