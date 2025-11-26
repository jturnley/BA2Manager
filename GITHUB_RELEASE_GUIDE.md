# GitHub Release Guide

This guide walks through creating the GitHub releases for BA2 Manager v2.0.0 and CC-Packer v1.0.

## Prerequisites

✅ All code committed to git
✅ Build packages created and tested
✅ Release notes prepared
✅ Repository pushed to GitHub

## Release 1: BA2 Manager v2.0.0 - Production Release

### Step 1: Navigate to Releases
1. Go to https://github.com/jturnley/BA2Manager/releases
2. Click "Draft a new release"

### Step 2: Create Release Tag
- **Tag version:** `v2.0.0`
- **Target:** `main` branch
- **Release title:** `BA2 Manager v2.0.0 - Production Release`

### Step 3: Add Release Description
Copy the entire contents of `RELEASE_NOTES_v2.0.0.md` into the description field.

### Step 4: Upload Binary Assets
Click "Attach binaries" and upload:
1. `releases/v2.0.0/BA2_Manager_v2.0.0_Windows.zip` (35.55 MB)
   - Label: "BA2 Manager v2.0.0 - Windows Binary"
2. `releases/v2.0.0/BA2_Manager_v2.0.0_Source.zip` (0.30 MB)
   - Label: "BA2 Manager v2.0.0 - Source Code"

### Step 5: Publish
- ✅ Check "Set as the latest release"
- ✅ Check "Create a discussion for this release" (optional)
- Click "Publish release"

---

## Release 2: CC-Packer v1.0 - Initial Release

### Step 1: Navigate to Releases
1. Go to https://github.com/jturnley/BA2Manager/releases
2. Click "Draft a new release"

### Step 2: Create Release Tag
- **Tag version:** `cc-packer-v1.0`
- **Target:** `main` branch
- **Release title:** `CC-Packer v1.0 - Initial Release`

### Step 3: Add Release Description
Copy the entire contents of `CC_Packer/RELEASE_NOTES_v1.0.md` into the description field.

### Step 4: Upload Binary Assets
Click "Attach binaries" and upload:
1. `CC_Packer/release/v1.0/CC-Packer_v1.0_Windows.zip` (35.03 MB)
   - Label: "CC-Packer v1.0 - Windows Binary"
2. `CC_Packer/release/v1.0/CC-Packer_v1.0_Source.zip` (0.01 MB)
   - Label: "CC-Packer v1.0 - Source Code"

### Step 5: Publish
- ⬜ Uncheck "Set as the latest release" (BA2 Manager v2.0.0 should be latest)
- ✅ Check "Create a discussion for this release" (optional)
- Click "Publish release"

---

## Post-Release Verification

### BA2 Manager v2.0.0
- [ ] Release visible at https://github.com/jturnley/BA2Manager/releases/tag/v2.0.0
- [ ] Binary download link works
- [ ] Source download link works
- [ ] Release notes display correctly
- [ ] Tagged as "Latest"

### CC-Packer v1.0
- [ ] Release visible at https://github.com/jturnley/BA2Manager/releases/tag/cc-packer-v1.0
- [ ] Binary download link works
- [ ] Source download link works
- [ ] Release notes display correctly
- [ ] NOT tagged as "Latest"

---

## Command-Line Alternative (Using GitHub CLI)

If you have GitHub CLI installed, you can create releases from the command line:

### BA2 Manager v2.0.0
```bash
# Create the release
gh release create v2.0.0 \
  --title "BA2 Manager v2.0.0 - Production Release" \
  --notes-file RELEASE_NOTES_v2.0.0.md \
  releases/v2.0.0/BA2_Manager_v2.0.0_Windows.zip \
  releases/v2.0.0/BA2_Manager_v2.0.0_Source.zip
```

### CC-Packer v1.0
```bash
# Create the release (not latest)
gh release create cc-packer-v1.0 \
  --title "CC-Packer v1.0 - Initial Release" \
  --notes-file CC_Packer/RELEASE_NOTES_v1.0.md \
  --prerelease=false \
  CC_Packer/release/v1.0/CC-Packer_v1.0_Windows.zip \
  CC_Packer/release/v1.0/CC-Packer_v1.0_Source.zip

# Then set BA2 Manager as latest
gh release edit v2.0.0 --latest
```

---

## Additional Tasks

### Update README.md
Add links to the new releases:
```markdown
## Download

### BA2 Manager v2.0.0
- [Windows Binary](https://github.com/jturnley/BA2Manager/releases/download/v2.0.0/BA2_Manager_v2.0.0_Windows.zip)
- [Source Code](https://github.com/jturnley/BA2Manager/releases/download/v2.0.0/BA2_Manager_v2.0.0_Source.zip)

### CC-Packer v1.0
- [Windows Binary](https://github.com/jturnley/BA2Manager/releases/download/cc-packer-v1.0/CC-Packer_v1.0_Windows.zip)
- [Source Code](https://github.com/jturnley/BA2Manager/releases/download/cc-packer-v1.0/CC-Packer_v1.0_Source.zip)
```

### Nexus Mods
1. Upload `BA2_Manager_v2.0.0_Windows.zip` to Nexus
2. Upload `CC-Packer_v1.0_Windows.zip` as separate mod (or add-on)
3. Update descriptions with GitHub links
4. Add changelog entries

### Social Media / Community
- Reddit: r/FalloutMods
- Nexus Forums
- Discord communities
- ModDB (optional)

---

## Troubleshooting

### Upload Size Limits
If you encounter upload size limits:
- GitHub releases support files up to 2GB
- Current packages are ~35MB each, well within limits
- If needed, use external hosting and link in release notes

### Tag Already Exists
If a tag already exists:
```bash
# Delete local tag
git tag -d v2.0.0

# Delete remote tag
git push origin :refs/tags/v2.0.0

# Recreate tag
git tag v2.0.0
git push origin v2.0.0
```

### Release Notes Formatting
- GitHub uses Markdown rendering
- Preview before publishing
- Images can be added via URL or drag-drop
- Emojis are supported (✅, 🎉, etc.)

---

## Success Criteria

Both releases are successful when:
- ✅ Downloads work from GitHub
- ✅ Executables run without errors
- ✅ Release notes are accurate and complete
- ✅ Version numbers match everywhere
- ✅ Community can find and use the releases
