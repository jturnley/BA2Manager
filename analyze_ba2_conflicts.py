"""Analyze BA2 files for filename conflicts with different content.

Note: The merge functions now respect modlist.txt load order, so conflicts
are resolved according to actual mod priority rather than alphabetical order.
"""
import subprocess
import hashlib
from pathlib import Path
import shutil
from collections import defaultdict

data_path = Path(r"C:\Users\jturn\.Code\BA2 Manager\mo2_fo4\Portable\Data")
archive2 = Path(r"C:\Users\jturn\.Code\BA2 Manager\mo2_fo4\Archive2.exe")
temp_base = Path(r"C:\Users\jturn\.Code\BA2 Manager\ba2_analysis_temp")

# Get non-vanilla, non-CC main BA2s
main_ba2s = [
    f for f in data_path.glob("*.ba2")
    if "texture" not in f.name.lower()
    and not f.name.startswith("Fallout4")
    and not f.name.startswith("DLC")
    and not f.name.lower().startswith("cc")
]

print(f"Analyzing {len(main_ba2s)} main BA2 files:")
for ba2 in main_ba2s:
    print(f"  - {ba2.name}")
print()

# Create temp directory
if temp_base.exists():
    shutil.rmtree(temp_base)
temp_base.mkdir(parents=True)

# Track files: filename -> list of (ba2_name, hash, size)
file_tracker = defaultdict(list)

try:
    for ba2 in main_ba2s:
        print(f"Processing: {ba2.name}...")
        
        extract_path = temp_base / ba2.stem
        extract_path.mkdir(exist_ok=True)
        
        # Extract BA2
        result = subprocess.run(
            [str(archive2), str(ba2), f"-e={extract_path}"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"  Warning: Failed to extract {ba2.name}")
            continue
        
        # Get all extracted files and hash them
        for file_path in extract_path.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(extract_path)).lower()
                
                # Calculate MD5 hash
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                file_hash = hasher.hexdigest()
                
                file_tracker[rel_path].append({
                    'ba2': ba2.name,
                    'hash': file_hash,
                    'size': file_path.stat().st_size
                })
    
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # Find conflicts: same filename, different hashes
    conflicts = []
    for file_name, entries in file_tracker.items():
        if len(entries) > 1:
            unique_hashes = len(set(e['hash'] for e in entries))
            if unique_hashes > 1:
                conflicts.append({
                    'file': file_name,
                    'count': len(entries),
                    'versions': unique_hashes,
                    'details': entries
                })
    
    if not conflicts:
        print("✓ No conflicts found!")
        print("  All files with same names have identical content.")
        print("  Merging will be safe with modlist.txt load order priority.")
    else:
        print(f"⚠️ Found {len(conflicts)} files with DIFFERENT CONTENT:")
        print()
        
        for conflict in conflicts[:10]:  # Show first 10
            print(f"File: {conflict['file']}")
            print(f"  Appears in {conflict['count']} BA2s with {conflict['versions']} different versions:")
            for detail in conflict['details']:
                size_kb = detail['size'] / 1024
                print(f"    - {detail['ba2']}: {detail['hash'][:8]}... ({size_kb:.1f} KB)")
            print()
        
        if len(conflicts) > 10:
            print(f"... and {len(conflicts) - 10} more conflicts")
        
        print()
        print("Impact on merging:")
        print("  - Files will overwrite based on modlist.txt load order")
        print("  - Last loaded version wins (matching game behavior)")
        print("  - May cause unexpected behavior if mods modify same files differently")

finally:
    # Cleanup
    if temp_base.exists():
        shutil.rmtree(temp_base)
    print()
    print("Cleanup complete.")
