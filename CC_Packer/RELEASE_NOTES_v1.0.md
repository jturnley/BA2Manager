# CC-Packer v1.0 - Initial Release

**Release Date:** November 25, 2025

## 🎉 First Official Release

CC-Packer is a standalone tool designed to solve the "Too Many Plugins" problem for Fallout 4 Creation Club users. Merge all your CC content into unified archives to reduce plugin count and improve game performance.

## ✨ Key Features

### Core Functionality
- **Automatic Detection**: Finds Fallout 4 installation and Archive2.exe automatically
- **Smart Merging**: Merges all `cc*.ba2` files into unified archives
- **Crash Prevention**: Automatically splits large texture archives (>3GB) to prevent "Brown Face" bug
- **Safe Operation**: Backs up all original files before making changes
- **Easy Restore**: One-click restoration to original state
- **Simple GUI**: Clean, intuitive interface - no configuration needed

### What Gets Merged
- `cc*-Main.ba2` → `CCMerged-Main.ba2`
- `cc*-Textures.ba2` → `CCMerged-Textures.ba2` (auto-split if >3GB)
- `cc*-Geometry.ba2` → `CCMerged-Geometry.ba2`
- `cc*-Voices_en.ba2` → `CCMerged-Voices_en.ba2`
- All other archive types merged appropriately

## 📦 What's Included

### Binary Package (`CC-Packer_v1.0_Windows.zip`)
- `CCPacker.exe` - Ready-to-run executable
- `README.md` - Usage instructions
- `LICENSE` - MIT License

### Source Package (`CC-Packer_v1.0_Source.zip`)
- `main.py` - GUI application
- `merger.py` - Core merging logic
- `requirements.txt` - Python dependencies
- `CCPacker.spec` - PyInstaller build specification
- `build_exe.bat` - Build script
- `README.md` - Documentation
- `LICENSE` - MIT License

## 🔧 Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended for large merges
- **Disk Space**: 2x the size of your CC content (for backup + merged files)
- **Fallout 4**: With Creation Club content installed
- **Creation Kit**: Required for Archive2.exe (free download from Bethesda.net)

## 📥 Installation

### Binary (Recommended)
1. Download `CC-Packer_v1.0_Windows.zip`
2. Extract `CCPacker.exe` anywhere on your PC
3. Run `CCPacker.exe` - no installation needed!

### From Source
1. Download `CC-Packer_v1.0_Source.zip`
2. Install Python 3.8+ and dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`
4. Or build: `pyinstaller CCPacker.spec`

## 🚀 Quick Start

1. **Launch**: Double-click `CCPacker.exe`
2. **Auto-Detection**: Tool finds Fallout 4 and Archive2.exe automatically
3. **Merge**: Click "Merge CC Archives" button
4. **Wait**: Progress bar shows merging status (may take 5-15 minutes)
5. **Done**: Launch Fallout 4 and enjoy reduced plugin count!

### If Auto-Detection Fails
- Click "Browse..." buttons to manually select:
  - Fallout 4 Data folder
  - Archive2.exe location (usually in Creation Kit Tools folder)

## 💡 Why Use CC-Packer?

### The Problem
- Fallout 4 has a 255 plugin limit (ESM/ESP files)
- Each Creation Club item = 1 plugin
- With 70+ CC items, you're left with only ~180 slots for mods
- Game performance degrades with many small BA2 archives

### The Solution
- CC-Packer merges all CC archives into 4-6 unified files
- Reduces plugin count from 70+ to just 1 master plugin
- Improves game loading times
- Frees up plugin slots for your favorite mods
- Prevents "Brown Face" bug by auto-splitting large texture archives

## 🛡️ Safety Features

### Automatic Backup
- All original CC files backed up to `Data/CC_Backup/`
- Backup is timestamped for easy identification
- Can restore original state at any time

### Restore Function
- Click "Restore Original CC Archives" to undo merge
- Moves merged files to dated backup folder
- Restores all original CC files from backup
- Safe to run multiple times

### Validation
- Checks for required files before merging
- Verifies Archive2.exe functionality
- Warns if insufficient disk space
- Provides clear error messages

## ⚠️ Important Notes

1. **Close Fallout 4**: Game must be closed before merging
2. **Close Mod Managers**: Close MO2, Vortex, etc. before running
3. **Backup Saves**: Always backup your save games first (optional but recommended)
4. **Archive2.exe Required**: Download Creation Kit if you don't have it
5. **One-Time Process**: After merging, you're done! No need to run again unless you add more CC content

## 🔄 When to Re-Run

Re-run CC-Packer if you:
- Install new Creation Club content
- Restore original archives
- Change BA2 compression settings
- Experience issues with merged archives

## 📊 Performance Benefits

Typical Results:
- **Plugin Count**: 70+ → 1
- **Archive Count**: 280+ → 4-6
- **Load Times**: 10-30% faster
- **Available Plugin Slots**: +70 for your mods

## 🤝 Compatibility

### Compatible With
- ✅ All Creation Club content
- ✅ Mod Organizer 2
- ✅ Vortex Mod Manager
- ✅ Manual mod installation
- ✅ Any load order tool

### Not Compatible With
- ❌ Nexus Mod Manager (outdated)
- ❌ BA2 archives from regular mods (use BA2 Manager instead)

## 🐛 Known Issues

- **First Run**: May take 15-20 minutes for large CC collections
- **Progress Bar**: May appear stuck at high percentages (be patient!)
- **Texture Split**: Very large CC collections may create 2-3 texture archives

## 🆘 Troubleshooting

### "Archive2.exe not found"
- Install Creation Kit from Bethesda.net (free)
- Or manually select Archive2.exe location

### "Fallout 4 Data folder not found"
- Check if Fallout 4 is installed via Steam/GOG
- Manually browse to your Fallout 4/Data folder

### "Merge Failed"
- Close Fallout 4 completely
- Run as Administrator
- Check disk space (need 2x CC content size)
- Verify all CC BA2 files are present

### "Brown Face Bug After Merge"
- This shouldn't happen (we auto-split large archives)
- If it does, run "Restore" then contact support

## 📖 Documentation

- **README.md**: Detailed usage guide in source package
- GitHub: Full documentation and updates

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/jturnley/BA2Manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jturnley/BA2Manager/discussions)

## 📜 License

MIT License - Free to use, modify, and distribute. See LICENSE file.

## 🙏 Acknowledgments

- Bethesda for Fallout 4 and Creation Kit
- The Fallout 4 modding community
- All testers who helped validate this tool

## 🔮 Future Plans

- Linux/Proton support
- Command-line interface
- Custom merge options
- Integration with mod managers

---

**Note**: CC-Packer is a companion tool to BA2 Manager. For advanced BA2 operations, conflict detection, and mod archive management, check out BA2 Manager v2.0.0!

## Related Tools

- **BA2 Manager v2.0.0**: Full-featured BA2 archive manager for modders
  - Advanced conflict detection
  - Batch operations
  - MO2 integration
  - Custom merging rules
