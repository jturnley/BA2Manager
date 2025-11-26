import os
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

class CCMerger:
    def __init__(self):
        self.logger = logging.getLogger("CCPacker")
        logging.basicConfig(level=logging.INFO)

    def merge_cc_content(self, fo4_path, archive2_path, progress_callback):
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        temp_dir = data_path / "CC_Temp"
        
        if not data_path.exists():
            return {"success": False, "error": "Data folder not found."}

        # 1. Identify CC Files
        cc_files = list(data_path.glob("cc*.ba2"))
        if not cc_files:
            return {"success": False, "error": "No Creation Club (cc*.ba2) files found."}

        progress_callback(f"Found {len(cc_files)} CC archives.")

        # 2. Backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = backup_dir / timestamp
        current_backup.mkdir(parents=True, exist_ok=True)
        
        progress_callback(f"Backing up files to {current_backup}...")
        for f in cc_files:
            shutil.copy2(f, current_backup / f.name)

        # 3. Extract
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        general_dir = temp_dir / "General"
        textures_dir = temp_dir / "Textures"
        general_dir.mkdir()
        textures_dir.mkdir()

        main_ba2s = [f for f in cc_files if "texture" not in f.name.lower()]
        texture_ba2s = [f for f in cc_files if "texture" in f.name.lower()]

        # Extract Main
        for i, f in enumerate(main_ba2s):
            progress_callback(f"Extracting Main [{i+1}/{len(main_ba2s)}]: {f.name}")
            subprocess.run([archive2_path, str(f), f"-e={general_dir}"], check=True, capture_output=True)

        # Extract Textures
        for i, f in enumerate(texture_ba2s):
            progress_callback(f"Extracting Textures [{i+1}/{len(texture_ba2s)}]: {f.name}")
            subprocess.run([archive2_path, str(f), f"-e={textures_dir}"], check=True, capture_output=True)

        # 4. Repack Main
        output_name = "CCMerged"
        merged_main = data_path / f"{output_name} - Main.ba2"
        
        if list(general_dir.rglob("*")):
            progress_callback("Repacking Main Archive...")
            subprocess.run([archive2_path, str(general_dir), f"-c={merged_main}", "-f=General", f"-r={general_dir}"], check=True, capture_output=True)

        # 5. Repack Textures (Smart Splitting)
        texture_files = []
        for f in textures_dir.rglob("*"):
            if f.is_file():
                texture_files.append((f, f.stat().st_size))
        
        # 3GB Limit (approx 3.2GB uncompressed usually fits safely in 2GB compressed limit, but let's use the 3GB logic from main)
        # Main code used 7GB uncompressed limit for ~3.5GB compressed.
        # Let's be safe and use 3GB uncompressed -> ~1.5GB compressed to be super safe, or stick to the main code's logic.
        # The main code used: MAX_UNCOMPRESSED_SIZE = int(7.0 * 1024 * 1024 * 1024)
        # I will use that.
        MAX_SIZE = int(7.0 * 1024 * 1024 * 1024) 
        
        groups = []
        current_group = []
        current_size = 0
        
        for f_path, f_size in texture_files:
            if current_size + f_size > MAX_SIZE and current_group:
                groups.append(current_group)
                current_group = []
                current_size = 0
            current_group.append(f_path)
            current_size += f_size
        if current_group:
            groups.append(current_group)

        created_esls = []

        for idx, group in enumerate(groups):
            suffix = "" if idx == 0 else f"_Part{idx+1}"
            archive_name = f"{output_name}{suffix} - Textures.ba2"
            target_path = data_path / archive_name
            
            progress_callback(f"Repacking Textures Part {idx+1}/{len(groups)}...")
            
            # Move files to temp split dir
            split_dir = temp_dir / f"split_{idx}"
            split_dir.mkdir(exist_ok=True)
            
            for f_path in group:
                rel = f_path.relative_to(textures_dir)
                dest = split_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f_path, dest)
            
            subprocess.run([archive2_path, str(split_dir), f"-c={target_path}", "-f=DDS", f"-r={split_dir}"], check=True, capture_output=True)
            
            # Create ESL for this part
            esl_name = f"{output_name}{suffix}.esl"
            self._create_dummy_esl(data_path / esl_name)
            created_esls.append(esl_name)

        # 6. Add to plugins.txt
        progress_callback("Enabling plugins...")
        self._add_to_plugins_txt(created_esls)

        # 7. Cleanup
        progress_callback("Cleaning up...")
        for f in cc_files:
            f.unlink()
        shutil.rmtree(temp_dir)

        return {"success": True}

    def restore_backup(self, fo4_path, progress_callback):
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        
        if not backup_dir.exists():
            return {"success": False, "error": "No backup folder found."}
            
        # Find most recent backup
        backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
        if not backups:
            return {"success": False, "error": "No backups found."}
            
        latest_backup = backups[0]
        progress_callback(f"Restoring from {latest_backup.name}...")

        # Delete merged files
        merged_esls = []
        for f in data_path.glob("CCMerged*.*"):
            if f.suffix.lower() == ".esl":
                merged_esls.append(f.name)
            f.unlink()

        # Remove from plugins.txt
        self._remove_from_plugins_txt(merged_esls)

        # Restore files
        backup_files = list(latest_backup.glob("*"))
        for i, f in enumerate(backup_files):
            shutil.copy2(f, data_path / f.name)
            
        return {"success": True}

    def _get_plugins_txt(self):
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:
            return None
        return Path(local_app_data) / "Fallout4" / "plugins.txt"

    def _add_to_plugins_txt(self, esl_names):
        plugins_txt = self._get_plugins_txt()
        if not plugins_txt or not plugins_txt.parent.exists():
            return

        if not plugins_txt.exists():
            lines = []
        else:
            try:
                with open(plugins_txt, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [l.strip() for l in f.readlines()]
            except:
                return

        modified = False
        for esl in esl_names:
            entry = f"*{esl}"
            if entry not in lines and esl not in lines:
                lines.append(entry)
                modified = True
        
        if modified:
            try:
                with open(plugins_txt, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines))
            except Exception as e:
                self.logger.error(f"Failed to write plugins.txt: {e}")

    def _remove_from_plugins_txt(self, esl_names):
        plugins_txt = self._get_plugins_txt()
        if not plugins_txt or not plugins_txt.exists():
            return

        try:
            with open(plugins_txt, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f.readlines()]
        except:
            return

        new_lines = []
        modified = False
        for line in lines:
            clean_line = line.lstrip("*")
            if clean_line in esl_names:
                modified = True
                continue
            new_lines.append(line)

        if modified:
            try:
                with open(plugins_txt, 'w', encoding='utf-8') as f:
                    f.write("\n".join(new_lines))
            except Exception as e:
                self.logger.error(f"Failed to write plugins.txt: {e}")

    def _create_dummy_esl(self, path):
        # Minimal ESL Header
        data = bytearray()
        data.extend(b'TES4')
        data.extend(b'\x19\x00\x00\x00') # Size
        data.extend(b'\x00\x00\x00\x00') # Flags
        data.extend(b'\x00\x00\x00\x00') # ID
        data.extend(b'\x00\x00\x00\x00')
        data.extend(b'\x00\x00\x00\x00')
        data.extend(b'HEDR')
        data.extend(b'\x0c\x00')
        data.extend(b'\x3f\x99\x99\x9a') # 1.2
        data.extend(b'\x00\x00\x00\x00')
        data.extend(b'\x00\x00\x00\x00')
        data.extend(b'CNAM')
        data.extend(b'\x01\x00')
        data.extend(b'\x00')
        
        with open(path, 'wb') as f:
            f.write(data)
