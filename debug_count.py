import os
from pathlib import Path

root = Path(r"C:\Users\jturn\.Code\BA2 Manager\mo2_fo4")
mods_dir = root / "mods"
data_dir = root / "Portable/Data"

def count_ba2s():
    # 1. Scan Data
    data_ba2s = list(data_dir.glob("*.ba2"))
    
    main_count = 0
    dlc_count = 0
    cc_count = 0
    store_count = 0
    
    vanilla_names = set()
    
    for f in data_ba2s:
        name = f.name.lower()
        vanilla_names.add(name)
        
        if name.startswith("fallout4 - "):
            main_count += 1
        elif name.startswith("dlc"):
            dlc_count += 1
        elif name.startswith("cc"):
            cc_count += 1
        else:
            store_count += 1
            
    # 2. Scan Mods
    mod_ba2s = list(mods_dir.rglob("*.ba2"))
    
    new_mod_count = 0
    replacement_count = 0
    
    for f in mod_ba2s:
        name = f.name.lower()
        if name in vanilla_names:
            replacement_count += 1
        else:
            new_mod_count += 1
            
    total = main_count + dlc_count + cc_count + store_count + new_mod_count
    
    print(f"Main Game: {main_count}")
    print(f"DLC: {dlc_count}")
    print(f"Creation Club: {cc_count}")
    print(f"Creation Store: {store_count}")
    print(f"Mods (New): {new_mod_count}")
    print(f"Mods (Replacements): {replacement_count}")
    print(f"TOTAL ACTIVE BA2s: {total}")

if __name__ == "__main__":
    count_ba2s()
