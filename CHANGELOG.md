# Changelog - BA2 Manager Pro

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-11-23

### Added
- **Custom Mod Directory Support**: Application now reads `mod_directory` setting from ModOrganizer.ini when present, allowing users with custom mod directory configurations to use BA2 Manager without manual path configuration.
- **Active Mods Filtering**: BA2 count now only includes mods marked as active in MO2's modlist.txt, providing accurate counts of active BA2 archives rather than all installed mods.
- **Dual BA2 Categories**: BA2 files are now split into two categories based on filename:
  - **Main BA2s**: Files without "- Textures" in the name (0-255 limit)
  - **Texture BA2s**: Files with "- Textures" in the name (0-254 limit)
  - Each category has its own progress bar showing green when within limits and red when exceeded
  - Dual progress bars on the right side of the application provide real-time visual feedback

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
