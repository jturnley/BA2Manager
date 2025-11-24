# Changelog - BA2 Manager Pro

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-11-24

### Added
- **Granular BA2 Management**: Extract/restore Main and Texture BA2s independently per mod
- **Loose File Cleanup**: Automatically removes extracted loose files when all BA2s are restored
  - Critical for Fallout 4 as loose files always override BA2 contents
  - Preserves ESP/ESM plugins and meta.ini
  - Ensures mods are fully restored to their packaged state
- **Load Order Protection**: 
  - Automatic backup of modlist.txt and plugins.txt on startup (creates .bak files)
  - Application never modifies load order during normal operations (extract/restore)
  - Only writes to modlist.txt/plugins.txt when explicitly managing Creation Club content
- **Real-time CC Monitoring**: Detects Creation Club enable/disable events via file watcher
  - Updates BA2 counts immediately when CC content state changes
  - Updates Fallout4.ccc file to reflect active CC content
- **Red Progress Bar Warnings**: Progress bars turn red when BA2 limits are exceeded
  - Main BA2s: Red when >255
  - Texture BA2s: Red when >254
- **Plugins.txt Filtering**: Excludes mods with disabled plugins from BA2 counts
- **Atomic Extract Operations**: Uses temporary directories to prevent partial extraction failures
- **Backup Preservation**: Restore operations preserve backups (copy instead of move) until all BA2s are restored
- **Custom Mod Directory Support**: Automatically reads `mod_directory` setting from ModOrganizer.ini
  - Supports both absolute and relative paths
  - Handles @ByteArray() format
  - Falls back to default `mods` folder if not configured
- **Active Mods Filtering**: Only counts mods enabled in MO2's modlist.txt
- **Dual BA2 Categories**: 
  - Main BA2s: Files without "- Textures" (0-255 limit)
  - Texture BA2s: Files with "- Textures" (0-254 limit)
  - Dual color-coded progress bars
- **Single-Selection Tables**: Prevents multi-selection confusion in mod and CC tables
- **Type Annotations**: Complete type hints for better IDE support

### Fixed
- Restore operations now clean up loose files when all BA2s are present
- Backup integrity preserved during individual BA2 restorations
- Custom mod_directory from ModOrganizer.ini now properly detected
- Archive2.exe detection now only runs after MO2 is configured
- Archive2 auto-detection enhanced with 3-tier search (MO2, FO4, Registry)
- Backup methods now properly called during initialization

### Changed
- Comprehensive documentation updates across all files
- Improved error handling and logging
- Enhanced API reference with accurate method signatures
- Removed alphabetical CC repositioning (conflicts with MO2's management)

## [1.0.0] - 2025-11-21

### Added
- Initial public release
- BA2 file extraction and restoration functionality
- Nexus Mods integration with automatic link generation from mod metadata
- Support for Creation Club content management
- QTableWidget-based GUI for displaying mods with Nexus links
- Auto-detection of Mod Organizer 2, Fallout 4, and Archive2 installations
- Persistent configuration storage
- Comprehensive logging system

### Features
- Extract/restore BA2 archives
- View active mod count by category (DLC, Creation Club, Mods)
- Browse mod information with direct links to Nexus Mods
- Integrated settings panel for path configuration
- Backup management for extracted archives
