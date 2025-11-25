# BA2 Manager Pro v2.0.0-beta.7 Release Notes

## Critical Fix: Texture Loading Issue Resolved

### What Was Fixed

**Root Cause Identified:** The 4GB splitting algorithm in beta.1-4 was breaking texture loading by separating related texture files across multiple archives.

**The Problem:**
- Previous algorithm sorted ALL texture files by size (largest to smallest)
- Files were then bin-packed into archives based on a 7GB uncompressed threshold
- This size-based approach **separated related textures** from the same CC item/mod
- Example: `vault_suit_d.dds` (diffuse map) ended up in `Textures1.ba2` while `vault_suit_n.dds` (normal map) went into `Textures2.ba2`
- Fallout 4's engine expects related textures to be together, resulting in pink/purple placeholder textures when they're split

**The Solution:**
- **CC Item Grouping:** Files are now grouped by their parent CC item/mod folder BEFORE splitting
- All textures belonging to the same Creation Club content stay together in the same archive
- Bin-packing now operates on entire CC item groups instead of individual files
- This preserves texture set coherence (diffuse, normal, specular maps remain together)

### Technical Changes

**New Splitting Algorithm:**
1. Groups all texture files by their CC item folder (e.g., `ccacxfo4001-vsuit`)
2. Calculates total size for each CC item group
3. Sorts groups by size (largest first) for efficient bin-packing
4. Packs entire groups into archives, keeping all related textures together
5. Only starts a new archive when adding the next group would exceed the 7GB threshold

**Benefits:**
- ✅ Maintains texture set integrity (no more pink textures!)
- ✅ Still splits large texture sets when needed (prevents 4GB+ BA2 files)
- ✅ Efficient packing (largest-first still applies to groups)
- ✅ Works with Mod Organizer 2 integration

### What to Test

1. **Texture Loading:** Verify all CC content displays textures correctly (no pink/purple placeholders)
2. **Archive Sizes:** Confirm split archives are under 4GB each
3. **Load Times:** Check that game loading performance is acceptable
4. **MO2 Integration:** Ensure merged BA2s load properly through Mod Organizer 2

### Changes from Beta.6

- **Re-enabled 4GB splitting** with CC item coherence preservation
- **Added type hints** for better code quality (`defaultdict`, typed dictionaries)
- **Enhanced logging** showing CC item grouping details
- **Improved debug output** listing largest CC groups being packed

### Usage Notes

- The merge will now create 1+ texture archives depending on your CC content size
- Each archive maintains CC item boundaries (never splits a single mod's textures)
- Archive names: `CCMerged - Textures.ba2` (single) or `CCMerged - Textures1.ba2`, `CCMerged - Textures2.ba2`, etc. (multiple)
- If a single CC item exceeds 7GB uncompressed, it will be placed in its own archive

### Testing Checklist

Before using in production:
- [ ] Run merge with your full CC collection
- [ ] Check log file for grouping information
- [ ] Verify archive sizes (should be ~3.5GB each when split)
- [ ] Launch Fallout 4 and visit locations with CC content
- [ ] Confirm textures load correctly (vault suit, armor, weapons, etc.)
- [ ] Test save/load functionality
- [ ] Monitor game stability

### Known Issues

None currently identified. This beta specifically addresses the texture loading issue reported in beta.4-5.

### Rollback Instructions

If you encounter issues:
1. Use the "Restore Original CC BA2s" button in the GUI
2. This will remove merged files and restore your original 338+ individual BA2 files
3. Your backups are stored in `BA2_Manager_Backups/CC_Merge_Backup/`

### Next Steps

If beta.7 testing is successful:
- Final v2.0.0 release with all features validated
- Documentation updates
- GitHub release with production-ready executable

---

**Version:** 2.0.0-beta.7  
**Date:** November 25, 2025  
**Focus:** Fix texture loading via CC item grouping in split algorithm
