# v2.0.0 Beta 9 Release Notes

## New Features
- **CC Packer Standalone**: Introduced a new standalone application `CC Packer` located in the `CC_Packer` directory.
    - Independent of Mod Organizer 2.
    - Automatically detects Fallout 4 and Archive2 paths.
    - Merges all Creation Club content into unified archives.
    - **Smart Splitting**: Automatically splits large texture archives (>3GB) to prevent game crashes.
    - **Auto-Plugin Management**: Automatically adds/removes `CCMerged.esl` entries in `plugins.txt`.
    - **Backup & Restore**: Full backup and restore functionality.

## Changes
- **Core Logic**: The smart splitting logic developed for the main application has been ported and adapted for the standalone tool.

## Installation (CC Packer)
1. Navigate to the `CC_Packer` folder.
2. Run `build_exe.bat` to create the executable (requires Python and PyInstaller).
3. Or run `python main.py` directly.
