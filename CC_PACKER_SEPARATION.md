# CC-Packer Separation Notice

**Date:** November 25, 2025

## What Changed

CC-Packer has been moved to its own standalone Git repository for better organization and independent versioning.

### New Repository
- **URL:** https://github.com/jturnley/CC-Packer
- **Version:** v1.0.0
- **Status:** Production ready

### Why the Change?

CC-Packer serves a different audience and use case than BA2 Manager:
- **CC-Packer**: Simple, focused tool for merging Creation Club content
- **BA2 Manager**: Advanced archive management tool for modders

Separating them allows:
- Independent release cycles
- Focused documentation for each tool
- Clearer project structure
- Easier maintenance

### What This Means for Users

**If you use CC-Packer:**
- Download from the new repository: https://github.com/jturnley/CC-Packer/releases
- All features remain the same
- Continued support and updates

**If you use BA2 Manager:**
- No changes to BA2 Manager functionality
- Continue using BA2 Manager as before
- CC-Packer is now a recommended companion tool

### Migration Path

The `CC_Packer/` folder in this repository is kept for historical reference but will not receive updates. All future CC-Packer development happens in the new repository.

### Related Projects

- **[CC-Packer](https://github.com/jturnley/CC-Packer)** - Standalone CC archive merger
- **[BA2 Manager](https://github.com/jturnley/BA2Manager)** - Full-featured BA2 archive manager

Both tools complement each other:
- Use CC-Packer for quick CC content merging
- Use BA2 Manager for advanced archive operations, conflict detection, and batch processing
