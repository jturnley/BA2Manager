# CC Packer (Standalone)

A simple, standalone tool to merge Fallout 4 Creation Club content into unified archives, reducing plugin count and improving load times.

## Features

- **Automatic Detection**: Finds your Fallout 4 installation and Archive2.exe.
- **Smart Merging**: Merges all `cc*.ba2` files in your Data folder.
- **Crash Prevention**: Automatically splits large texture archives (>3GB) to prevent the "Brown Face" bug and crashes.
- **Safety**: Backs up all original files to `Data/CC_Backup` before making changes.
- **Restore**: Easily revert to the original state.

## Requirements

- Windows 10/11
- Fallout 4
- Creation Kit (for `Archive2.exe`)

## Usage

1. Run `python main.py`.
2. Ensure the paths for Fallout 4 and Archive2.exe are correct.
3. Click **Merge CC Content**.
4. Wait for the process to finish.
5. To revert, click **Restore Backup**.
