# BA2 Manager v1.1.4 - Multiple MO2 Profile Support

## 🆕 New Features

### Multiple Profile Support
- **Automatic Profile Detection**: BA2 Manager now automatically detects and uses the selected profile from `ModOrganizer.ini` when multiple profiles exist
- **Dynamic Profile Switching**: Reads `modlist.txt` and `plugins.txt` from the active MO2 profile instead of being hardcoded to "Default"
- **Smart Fallback**: Automatically falls back to "Default" profile when only one profile exists or when the selected profile cannot be determined

## ✨ Improvements

- **Better MO2 Integration**: Respects MO2's profile system for improved workflow integration
- **Accurate BA2 Counting**: BA2 counts now reflect the actual active profile's mod configuration
- **Intelligent Path Resolution**: More robust profile path detection based on MO2 installation structure

## 🔧 Technical Details

- Added `_get_selected_profile()` method to BA2Handler for intelligent profile detection
- Updated `_get_modlist_path()` and `_get_plugins_path()` to use dynamic profile names
- Profile detection checks for multiple profiles before reading `selected_profile` setting
- Handles `@ByteArray()` encoding used by Qt in ModOrganizer.ini

## 📦 Installation

1. Download `BA2_Manager_v1.1.4_Windows.zip`
2. Extract to your preferred location (recommended: inside MO2 directory)
3. Run `ba2-manager.exe`
4. Configure paths in Settings tab on first run

## ⚠️ Pre-Release Notice

This is a pre-release version for testing the new multiple profile support feature. Please report any issues on GitHub.

## 🔗 Previous Releases

- v1.1.3 - Critical safety fixes and error handling
- v1.1.2 - Removed orphaned dead code
- v1.1.1 - Fixed legacy progress bar code
- v1.1.0 - Full Python GUI implementation

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/jturnley/BA2Manager/blob/main/CHANGELOG.md) for complete version history.
