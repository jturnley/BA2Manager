"""BA2 file handler for core operations

This module handles all BA2 (Bethesda Archive 2) file operations for Fallout 4.
It provides the core functionality for:

1. COUNTING BA2 FILES
   - Scans Fallout 4 Data directory for base game BA2s
   - Counts mods BA2s from MO2 mods directory (recursively)
   - Categorizes by type: Main, DLC, CC (Creation Club), Creation Store, Mods
   - Tracks vanilla replacements (mod BA2s replacing base game files)
   - Reads Fallout4.ccc to determine which CC content is active
   - MATCHING LOGIC: Exactly replicates PowerShell script counting

2. LISTING MOD BA2s
   - Returns all BA2 files found in MO2 mods directory
   - Provides file size and mod name information
   - Used by GUI to populate mod selection list

3. FUTURE: EXTRACTION/RESTORATION
   - Will integrate Archive2.exe for BA2 compression/decompression
   - Backend for "Extract" and "Restore" operations

KEY CONCEPTS:
- BA2 = Bethesda Archive 2 (compressed archive format)
- Main BA2s = Base game files (fallout4 - *.ba2)
- DLC BA2s = DLC content (dlc*.ba2)
- CC BA2s = Creation Club content (cc*.ba2, active if in Fallout4.ccc)
- Mod BA2s = Community mod archives in mods folder
- Vanilla Replacements = Mods with same filename as base game BA2s
- Extraction = Decompressing BA2s to loose files (uses disk space)
- Restoration = Recompressing BA2s (frees disk space)
"""

import os
import re
import subprocess
import logging
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class BA2Info:
    """
    Data structure representing a single mod with its BA2 files.
    
    Attributes:
        mod_name: Display name of the mod (directory name)
        has_main_ba2: Whether this mod has a main BA2 file
        has_texture_ba2: Whether this mod has a texture BA2 file
        main_extracted: Whether the main BA2 is currently extracted
        texture_extracted: Whether the texture BA2 is currently extracted
        total_size: Combined size of all BA2 files in bytes
        has_backup: Whether a backup exists for this mod
        nexus_url: Optional URL to the mod's Nexus page
    
    Used by list_ba2_mods() to return mod BA2 information to the GUI.
    """
    mod_name: str
    has_main_ba2: bool = False
    has_texture_ba2: bool = False
    main_extracted: bool = False
    texture_extracted: bool = False
    total_size: int = 0
    has_backup: bool = False
    nexus_url: Optional[str] = None


class BA2Handler:
    """
    Core handler for all BA2 file operations.
    
    MAIN RESPONSIBILITIES:
    1. Count BA2 files across all sources (base game, DLC, CC, mods)
    2. List mod BA2s for GUI selection
    3. Interface with Archive2.exe for future extraction/restoration
    
    INITIALIZATION PARAMETERS:
    - archive2_path: Path to Archive2.exe (not required for counting)
    - mo2_dir: Path to MO2 mods directory (where mod BA2s are stored)
    - log_file: Path to log file for operation tracking
    
    STATE TRACKING:
    - logger: FileHandler logging all operations to ba2-manager.log
    - failed_extractions: List of BA2s that failed to extract (for error reporting)
    
    CONSTANTS:
    - CC_NAMES: Mapping of CC plugin IDs to display names
    - VANILLA_BA2S: List of official Fallout 4 base game BA2 filenames
    """
    
    # CREATION CLUB MAPPING
    # Maps Creation Club plugin IDs to their display names and BA2 count
    # Used to identify and categorize CC content in base game Data folder
    CC_NAMES = {
        "ccacxfo4001": {"name": "Vault Suit Customization", "ba2_count": 2},
        "ccawnfo4001": {"name": "Graphic T-Shirt Pack", "ba2_count": 2},
        "ccawnfo4002": {"name": "Faction Clothing Pack", "ba2_count": 2},
        "ccbgsfo4001": {"name": "Pip-Boy Paint - Black", "ba2_count": 2},
        "ccbgsfo4002": {"name": "Pip-Boy Paint - Blue", "ba2_count": 2},
        "ccbgsfo4003": {"name": "Pip-Boy Paint - Desert Camo", "ba2_count": 2},
        "ccbgsfo4004": {"name": "Pip-Boy Paint - Swamp Camo", "ba2_count": 2},
        "ccbgsfo4005": {"name": "Pip-Boy Paint - Aquatic Camo", "ba2_count": 2},
        "ccbgsfo4006": {"name": "Pip-Boy Paint - Chrome", "ba2_count": 2},
        "ccbgsfo4008": {"name": "Pip-Boy Paint - Green", "ba2_count": 2},
        "ccbgsfo4009": {"name": "Pip-Boy Paint - Orange", "ba2_count": 2},
        "ccbgsfo4010": {"name": "Pip-Boy Paint - Pink", "ba2_count": 2},
        "ccbgsfo4011": {"name": "Pip-Boy Paint - Purple", "ba2_count": 2},
        "ccbgsfo4012": {"name": "Pip-Boy Paint - Red", "ba2_count": 2},
        "ccbgsfo4013": {"name": "Pip-Boy Paint - Tan", "ba2_count": 2},
        "ccbgsfo4014": {"name": "Pip-Boy Paint - Silver White", "ba2_count": 2},
        "ccbgsfo4015": {"name": "Pip-Boy Paint - Yellow", "ba2_count": 2},
        "ccbgsfo4016": {"name": "Pip-Boy Paint - Prey (Corvega)", "ba2_count": 2},
        "ccbgsfo4018": {"name": "Prototype Gauss Rifle", "ba2_count": 2},
        "ccbgsfo4019": {"name": "Chinese Stealth Armor", "ba2_count": 2},
        "ccbgsfo4020": {"name": "Power Armor Paint - Onyx", "ba2_count": 2},
        "ccbgsfo4021": {"name": "Power Armor Paint - Blue", "ba2_count": 2},
        "ccbgsfo4022": {"name": "Power Armor Paint - Desert Camo", "ba2_count": 2},
        "ccbgsfo4023": {"name": "Power Armor Paint - Swamp Camo", "ba2_count": 2},
        "ccbgsfo4024": {"name": "Power Armor Paint - Aquatic Camo", "ba2_count": 2},
        "ccbgsfo4025": {"name": "Power Armor Paint - Chrome", "ba2_count": 2},
        "ccbgsfo4027": {"name": "Power Armor Paint - Green", "ba2_count": 2},
        "ccbgsfo4028": {"name": "Power Armor Paint - Orange", "ba2_count": 2},
        "ccbgsfo4029": {"name": "Power Armor Paint - Pink", "ba2_count": 2},
        "ccbgsfo4030": {"name": "Power Armor Paint - Purple", "ba2_count": 2},
        "ccbgsfo4031": {"name": "Power Armor Paint - Red", "ba2_count": 2},
        "ccbgsfo4032": {"name": "Power Armor Paint - Tan", "ba2_count": 2},
        "ccbgsfo4033": {"name": "Power Armor Paint - White", "ba2_count": 2},
        "ccbgsfo4034": {"name": "Power Armor Paint - Yellow", "ba2_count": 2},
        "ccbgsfo4035": {"name": "Pint-Sized Slasher", "ba2_count": 2},
        "ccbgsfo4036": {"name": "TransDOGrifier", "ba2_count": 2},
        "ccbgsfo4038": {"name": "Horse Power Armor", "ba2_count": 2},
        "ccbgsfo4040": {"name": "Virtual Workshops", "ba2_count": 2},
        "ccbgsfo4041": {"name": "Doom Classic Marine Armor", "ba2_count": 2},
        "ccbgsfo4042": {"name": "Doom BFG", "ba2_count": 2},
        "ccbgsfo4044": {"name": "Hellfire Power Armor", "ba2_count": 2},
        "ccbgsfo4045": {"name": "Arcade Workshop Pack", "ba2_count": 2},
        "ccbgsfo4046": {"name": "Tesla Cannon", "ba2_count": 2},
        "ccbgsfo4047": {"name": "Quake Thunderbolt", "ba2_count": 2},
        "ccbgsfo4048": {"name": "Fantasy Hero Set", "ba2_count": 2},
        "ccbgsfo4049": {"name": "Brahmin Armor", "ba2_count": 2},
        "ccbgsfo4050": {"name": "Dog Skin - Border Collie", "ba2_count": 2},
        "ccbgsfo4051": {"name": "Dog Skin - Boxer", "ba2_count": 2},
        "ccbgsfo4052": {"name": "Dog Skin - Dalmatian", "ba2_count": 2},
        "ccbgsfo4053": {"name": "Dog Skin - Golden Retriever", "ba2_count": 2},
        "ccbgsfo4054": {"name": "Dog Skin - Great Dane", "ba2_count": 2},
        "ccbgsfo4055": {"name": "Dog Skin - Husky", "ba2_count": 2},
        "ccbgsfo4056": {"name": "Dog Skin - Black Labrador", "ba2_count": 2},
        "ccbgsfo4057": {"name": "Dog Skin - Yellow Labrador", "ba2_count": 2},
        "ccbgsfo4058": {"name": "Dog Skin - Chocolate Labrador", "ba2_count": 2},
        "ccbgsfo4059": {"name": "Dog Skin - Pitbull", "ba2_count": 2},
        "ccbgsfo4060": {"name": "Dog Skin - Rottweiler", "ba2_count": 2},
        "ccbgsfo4061": {"name": "Dog Skin - Shiba Inu", "ba2_count": 2},
        "ccbgsfo4062": {"name": "Pip-Boy Paint - Patriotic", "ba2_count": 2},
        "ccbgsfo4063": {"name": "Power Armor Paint - Patriotic", "ba2_count": 2},
        "ccbgsfo4070": {"name": "Pip-Boy Paint - Abraxo", "ba2_count": 2},
        "ccbgsfo4071": {"name": "Pip-Boy Paint - ArcJet", "ba2_count": 2},
        "ccbgsfo4072": {"name": "Pip-Boy Paint - Grognak", "ba2_count": 2},
        "ccbgsfo4073": {"name": "Pip-Boy Paint - Manta Man", "ba2_count": 2},
        "ccbgsfo4074": {"name": "Pip-Boy Paint - The Inspector", "ba2_count": 2},
        "ccbgsfo4075": {"name": "Pip-Boy Paint - Silver Shroud", "ba2_count": 2},
        "ccbgsfo4076": {"name": "Pip-Boy Paint - Mistress of Mystery", "ba2_count": 2},
        "ccbgsfo4077": {"name": "Pip-Boy Paint - Red Rocket", "ba2_count": 2},
        "ccbgsfo4078": {"name": "Pip-Boy Paint - Reilly's Rangers", "ba2_count": 2},
        "ccbgsfo4079": {"name": "Pip-Boy Paint - Vim!", "ba2_count": 2},
        "ccbgsfo4080": {"name": "Pip-Boy Paint - Pop", "ba2_count": 2},
        "ccbgsfo4081": {"name": "Pip-Boy Paint - Phenol Resin", "ba2_count": 2},
        "ccbgsfo4082": {"name": "Pip-Boy Paint - Five-Star Red", "ba2_count": 2},
        "ccbgsfo4083": {"name": "Pip-Boy Paint - Art Deco", "ba2_count": 2},
        "ccbgsfo4084": {"name": "Pip-Boy Paint - Adventure", "ba2_count": 2},
        "ccbgsfo4085": {"name": "Pip-Boy Paint - Hawaii", "ba2_count": 2},
        "ccbgsfo4086": {"name": "Pip-Boy Paint - Corvega", "ba2_count": 2},
        "ccbgsfo4087": {"name": "Pip-Boy Paint - Haida", "ba2_count": 2},
        "ccbgsfo4089": {"name": "Pip-Boy Paint - Neon Sunrise", "ba2_count": 2},
        "ccbgsfo4090": {"name": "Pip-Boy Paint - Tribal", "ba2_count": 2},
        "ccbgsfo4091": {"name": "Armor Skin - Bats", "ba2_count": 2},
        "ccbgsfo4092": {"name": "Armor Skin - Aquatic Camo", "ba2_count": 2},
        "ccbgsfo4093": {"name": "Armor Skin - Swamp Camo", "ba2_count": 2},
        "ccbgsfo4094": {"name": "Armor Skin - Desert Camo", "ba2_count": 2},
        "ccbgsfo4095": {"name": "Armor Skin - Children of Atom", "ba2_count": 2},
        "ccbgsfo4096": {"name": "Armor Skin - Enclave", "ba2_count": 2},
        "ccbgsfo4097": {"name": "Armor Skin - Jack O'Lantern", "ba2_count": 2},
        "ccbgsfo4098": {"name": "Armor Skin - Pickman", "ba2_count": 2},
        "ccbgsfo4099": {"name": "Armor Skin - Reilly's Rangers", "ba2_count": 2},
        "ccbgsfo4101": {"name": "Armor Skin - Shi", "ba2_count": 2},
        "ccbgsfo4103": {"name": "Armor Skin - Tunnel Snakes", "ba2_count": 2},
        "ccbgsfo4104": {"name": "Weapon Skin - Bats", "ba2_count": 2},
        "ccbgsfo4105": {"name": "Weapon Skin - Aquatic Camo", "ba2_count": 2},
        "ccbgsfo4106": {"name": "Weapon Skin - Swamp Camo", "ba2_count": 2},
        "ccbgsfo4107": {"name": "Weapon Skin - Desert Camo", "ba2_count": 2},
        "ccbgsfo4108": {"name": "Weapon Skin - Children of Atom", "ba2_count": 2},
        "ccbgsfo4110": {"name": "Weapon Skin - Enclave", "ba2_count": 2},
        "ccbgsfo4111": {"name": "Weapon Skin - Jack O'Lantern", "ba2_count": 2},
        "ccbgsfo4112": {"name": "Weapon Skin - Pickman", "ba2_count": 2},
        "ccbgsfo4113": {"name": "Weapon Skin - Reilly's Rangers", "ba2_count": 2},
        "ccbgsfo4114": {"name": "Weapon Skin - Shi", "ba2_count": 2},
        "ccbgsfo4115": {"name": "X-02 Power Armor", "ba2_count": 2},
        "ccbgsfo4116": {"name": "Heavy Incinerator", "ba2_count": 2},
        "ccbgsfo4117": {"name": "Capital Wasteland Mercenaries", "ba2_count": 2},
        "ccbgsfo4118": {"name": "Weapon Skin - Tunnel Snakes", "ba2_count": 2},
        "ccbgsfo4119": {"name": "Cyber Dog", "ba2_count": 2},
        "ccbgsfo4120": {"name": "Power Armor Paint - Pitt Raider", "ba2_count": 2},
        "ccbgsfo4121": {"name": "Power Armor Paint - Air Force", "ba2_count": 2},
        "ccbgsfo4122": {"name": "Power Armor Paint - Scorched Sierra", "ba2_count": 2},
        "ccbgsfo4123": {"name": "Power Armor Paint - Inferno", "ba2_count": 2},
        "ccbgsfo4124": {"name": "Repurposed Power Armor Helmets", "ba2_count": 2},
        "cccrsfo4001": {"name": "Pip-Boy Paint - Children of Atom", "ba2_count": 2},
        "cceejfo4001": {"name": "Home Decor Workshop Pack", "ba2_count": 2},
        "cceejfo4002": {"name": "Nuka-Cola Collector Workshop", "ba2_count": 2},
        "ccfrsfo4001": {"name": "Handmade Shotgun", "ba2_count": 2},
        "ccfrsfo4002": {"name": "Anti-Materiel Rifle", "ba2_count": 2},
        "ccfrsfo4003": {"name": "CR-74L Combat Rifle", "ba2_count": 2},
        "ccfsvfo4001": {"name": "Modular Military Backpack", "ba2_count": 2},
        "ccfsvfo4002": {"name": "Modern Furniture Workshop Pack", "ba2_count": 2},
        "ccfsvfo4003": {"name": "Coffee and Donuts Workshop Pack", "ba2_count": 2},
        "ccfsvfo4004": {"name": "Virtual Workshops - GNR Plaza", "ba2_count": 2},
        "ccfsvfo4005": {"name": "Virtual Workshops - Desert Island", "ba2_count": 2},
        "ccfsvfo4006": {"name": "Virtual Workshops - Wasteland", "ba2_count": 2},
        "ccfsvfo4007": {"name": "Halloween Workshop Pack", "ba2_count": 2},
        "ccgcafo4001": {"name": "Weapon Skin - Army", "ba2_count": 2},
        "ccgcafo4002": {"name": "Weapon Skin - Atom Cats", "ba2_count": 2},
        "ccgcafo4003": {"name": "Weapon Skin - Brotherhood of Steel", "ba2_count": 2},
        "ccgcafo4004": {"name": "Weapon Skin - Gunners", "ba2_count": 2},
        "ccgcafo4005": {"name": "Weapon Skin - Hot Rod Pink Flames", "ba2_count": 2},
        "ccgcafo4006": {"name": "Weapon Skin - Hot Rod Shark", "ba2_count": 2},
        "ccgcafo4007": {"name": "Weapon Skin - Hot Rod Red Flames", "ba2_count": 2},
        "ccgcafo4008": {"name": "Weapon Skin - The Institute", "ba2_count": 2},
        "ccgcafo4009": {"name": "Weapon Skin - Minutemen", "ba2_count": 2},
        "ccgcafo4010": {"name": "Weapon Skin - Railroad", "ba2_count": 2},
        "ccgcafo4011": {"name": "Weapon Skin - Vault-Tec", "ba2_count": 2},
        "ccgcafo4012": {"name": "Armor Skin - Atom Cats", "ba2_count": 2},
        "ccgcafo4013": {"name": "Armor Skin - Brotherhood of Steel", "ba2_count": 2},
        "ccgcafo4014": {"name": "Armor Skin - Gunners", "ba2_count": 2},
        "ccgcafo4015": {"name": "Armor Skin - Hot Rod Pink Flames", "ba2_count": 2},
        "ccgcafo4016": {"name": "Armor Skin - Hot Rod Shark", "ba2_count": 2},
        "ccgcafo4017": {"name": "Armor Skin - The Institute", "ba2_count": 2},
        "ccgcafo4018": {"name": "Armor Skin - Minutemen", "ba2_count": 2},
        "ccgcafo4019": {"name": "Armor Skin - Nuka Cherry", "ba2_count": 2},
        "ccgcafo4020": {"name": "Armor Skin - Railroad", "ba2_count": 2},
        "ccgcafo4021": {"name": "Armor Skin - Hot Rod Red Flames", "ba2_count": 2},
        "ccgcafo4022": {"name": "Armor Skin - Vault-Tec", "ba2_count": 2},
        "ccgcafo4023": {"name": "Armor Skin - Army", "ba2_count": 2},
        "ccgcafo4024": {"name": "Institute Plasma Weapons", "ba2_count": 2},
        "ccgcafo4025": {"name": "Power Armor Paint - Gunners vs. Minutemen", "ba2_count": 2},
        "ccgrcfo4001": {"name": "Pip-Boy Paint - Grey Tortoise", "ba2_count": 2},
        "ccgrcfo4002": {"name": "Pip-Boy Paint - Green Vim", "ba2_count": 2},
        "ccjvdfo4001": {"name": "Holiday Workshop Pack", "ba2_count": 2},
        "cckgjfo4001": {"name": "Settlement Ambush Kit", "ba2_count": 2},
        "ccotmfo4001": {"name": "Enclave Remnants", "ba2_count": 2},
        "ccqdrfo4001": {"name": "Sentinel Control System Companion", "ba2_count": 2},
        "ccrpsfo4001": {"name": "Sea Scavengers", "ba2_count": 2},
        "ccrzrfo4001": {"name": "Tunnel Snakes Rule!", "ba2_count": 2},
        "ccrzrfo4002": {"name": "Zetan Arsenal", "ba2_count": 2},
        "ccrzrfo4003": {"name": "Pip-Boy Paint - Overseer's Edition", "ba2_count": 2},
        "ccrzrfo4004": {"name": "Pip-Boy Paint - Institute", "ba2_count": 2},
        "ccsbjfo4001": {"name": "Solar Cannon", "ba2_count": 2},
        "ccsbjfo4002": {"name": "Manwell Rifle Set", "ba2_count": 2},
        "ccsbjfo4003": {"name": "Makeshift Weapon Pack", "ba2_count": 2},
        "ccsbjfo4004": {"name": "Ion Gun", "ba2_count": 2},
        "ccswkfo4001": {"name": "Captain Cosmos", "ba2_count": 2},
        "ccswkfo4002": {"name": "Pip-Boy Paint - Nuka-Cola", "ba2_count": 2},
        "ccswkfo4003": {"name": "Pip-Boy Paint - Nuka-Cola Quantum", "ba2_count": 2},
        "cctosfo4001": {"name": "Virtual Workshop: Grid World", "ba2_count": 2},
        "cctosfo4002": {"name": "Neon Flats", "ba2_count": 2},
        "ccvltfo4001": {"name": "Noir Penthouse", "ba2_count": 2},
        "ccygpfo4001": {"name": "Pip-Boy Paint - Cruiser", "ba2_count": 2},
        "cczsef04001": {"name": "Charlestown Condo", "ba2_count": 2},
        "cczsefo4002": {"name": "Shroud Manor", "ba2_count": 2},
    }
    
    # VANILLA BA2S - Official Fallout 4 base game files
    # Used to:
    # 1. Identify vanilla replacements in mod folders
    # 2. Categorize base game BA2s by type (main vs texture)
    VANILLA_BA2S = [
        "Fallout4.ba2",
        "Fallout4 - Textures.ba2",
        "Fallout4 - Textures1.ba2",
        "Fallout4 - Textures2.ba2",
        "Fallout4 - Textures3.ba2",
        "Fallout4 - Textures4.ba2",
        "Fallout4 - Textures5.ba2",
        "Fallout4 - Textures6.ba2",
        "Fallout4 - Textures7.ba2",
        "Fallout4 - Textures8.ba2",
        "Fallout4 - Textures9.ba2",
        "Fallout4 - Voices.ba2",
        "Fallout4 - Startup.ba2",
        "Fallout4 - Interface.ba2",
        "Fallout4 - Meshes.ba2",
        "Fallout4 - MeshesExtra.ba2",
        "Fallout4 - Misc.ba2",
        "Fallout4 - Sounds.ba2",
        "Fallout4 - Materials.ba2",
        "Fallout4 - Animations.ba2",
        "DLCRobot.ba2",
        "DLCRobot - Textures.ba2",
        "DLCworkshop01.ba2",
        "DLCworkshop01 - Textures.ba2",
        "DLCCoast.ba2",
        "DLCCoast - Textures.ba2",
        "DLCNukaWorld.ba2",
        "DLCNukaWorld - Textures.ba2",
        "DLCworkshop02.ba2",
        "DLCworkshop02 - Textures.ba2",
        "DLCworkshop03.ba2",
        "DLCworkshop03 - Textures.ba2",
    ]
    
    def __init__(self, archive2_path: Optional[str] = None, mo2_dir: Optional[str] = None, backup_dir: Optional[str] = None, log_file: Optional[str] = None):
        r"""
        Initialize BA2 handler with paths and logging.
        
        PARAMETERS:
            archive2_path (str, optional): Full path to Archive2.exe
            mo2_dir (str, optional): Path to MO2 mods directory
            backup_dir (str, optional): Path to backup directory for extracted mods
            log_file (str, optional): Path to log file
        """
        self.archive2_path = archive2_path
        self.mo2_dir = mo2_dir or "mods"
        
        # Backup directory should be relative to MO2, not the application directory
        if backup_dir:
            self.backup_dir = backup_dir
        else:
            # Default: Create backup directory as sibling to mods directory
            mo2_path = Path(self.mo2_dir)
            if mo2_path.name == "mods" and mo2_path.parent.exists():
                # mo2_dir is the mods folder, use parent (MO2 root)
                self.backup_dir = str(mo2_path.parent / "BA2_Manager_Backups")
            else:
                # mo2_dir is something else, create backup alongside it
                self.backup_dir = str(mo2_path.parent / "BA2_Manager_Backups")
        
        self.log_file = log_file or "ba2-manager.log"
        self.failed_extractions = []
        # Initialize vanilla BA2 names with hardcoded list as fallback
        self.vanilla_ba2_names = set(name.lower() for name in self.VANILLA_BA2S)
        # Initialize mod tracking for partial extraction detection
        # Store in working directory (not temp dir) for persistence when running as executable
        self.modlist_file = Path("ba2_manager_modlist.json")
        self.mod_tracking = self._load_mod_tracking()
        
        # Setup logging
        import sys
        self.logger = logging.getLogger("BA2Handler")
        # Set log level based on config
        debug_logging = False
        try:
            from ba2_manager.config import Config
            config = Config()
            debug_logging = config.get("debug_logging", False)
        except Exception:
            pass
        self.logger.setLevel(logging.DEBUG if debug_logging else logging.INFO)
        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # Always log to working directory
        try:
            handler1 = logging.FileHandler("ba2-manager.log", mode='a')
            handler1.setLevel(logging.DEBUG)
            handler1.setFormatter(formatter)
            self.logger.addHandler(handler1)
        except Exception as e:
            print(f"Warning: Could not set up logging to ba2-manager.log: {e}")
        # Always log to /dist/ba2-manager.log
        try:
            handler2 = logging.FileHandler("dist/ba2-manager.log", mode='a')
            handler2.setLevel(logging.DEBUG)
            handler2.setFormatter(formatter)
            self.logger.addHandler(handler2)
        except Exception as e:
            print(f"Warning: Could not set up logging to dist/ba2-manager.log: {e}")
        # Always log to console
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        except Exception as e:
            print(f"Warning: Could not set up console logging: {e}")
        self.logger.info(f"BA2Handler initialized - mods_dir={self.mo2_dir}, log_file={self.log_file}, debug_logging={debug_logging}")
        
        # Create backups of modlist.txt and plugins.txt on startup
        self.backup_modlist()
        self.backup_plugins()
    
    def _load_mod_tracking(self) -> dict:
        """Load mod tracking data from ba2_manager_modlist.json file."""
        try:
            if self.modlist_file.exists():
                with open(self.modlist_file, 'r') as f:
                    data = json.load(f)
                    return data.get("mods", {})
        except Exception as e:
            self.logger.warning(f"Could not load mod tracking file: {e}")
        return {}
    
    def _save_mod_tracking(self):
        """Save mod tracking data to ba2_manager_modlist.json file."""
        try:
            data = {
                "version": "1.0",
                "description": "Tracks BA2 extraction states for mods",
                "mods": self.mod_tracking
            }
            with open(self.modlist_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved mod tracking to {self.modlist_file}")
        except Exception as e:
            self.logger.warning(f"Could not save mod tracking file: {e}")
    
    def _update_mod_tracking(self, current_mods: dict):
        """Update tracking with current mod states and clean up uninstalled mods."""
        from datetime import datetime
        
        # Update tracking for mods we currently see
        for mod_name, mod_data in current_mods.items():
            if mod_name not in self.mod_tracking:
                self.mod_tracking[mod_name] = {
                    "main_extracted": mod_data.get('main_extracted', False),
                    "texture_extracted": mod_data.get('texture_extracted', False),
                    "last_seen": datetime.now().isoformat()
                }
            else:
                # Update extraction states based on current detection
                self.mod_tracking[mod_name]['main_extracted'] = mod_data.get('main_extracted', False)
                self.mod_tracking[mod_name]['texture_extracted'] = mod_data.get('texture_extracted', False)
                self.mod_tracking[mod_name]['last_seen'] = datetime.now().isoformat()
        
        # Detect uninstalled mods by checking if they're in tracking but not in current_mods
        # These might have orphaned backups that should be cleaned up
        uninstalled_mods = set(self.mod_tracking.keys()) - set(current_mods.keys())
        if uninstalled_mods:
            self.logger.info(f"Detected uninstalled mods: {uninstalled_mods}. Orphaned backups may exist.")
            # In future: add cleanup logic here
        
        # Save updated tracking
        self._save_mod_tracking()
    

    def count_ba2_files(self, fo4_path: str) -> Dict[str, Any]:
        """
        Count BA2 files across all sources and categorize them.
        
        THIS IS THE CORE COUNTING LOGIC - Matches PowerShell script exactly.
        
        PROCESS:
        1. Read Fallout4.ccc to determine which CC plugins are ACTIVE
           - Only active CC BA2s count toward the total
        
        2. Scan base game Data folder (fo4_path/Data/)
           - Categorize by filename pattern:
             * Fallout4 - *.ba2 → MAIN (main game files)
             * DLC*.ba2 → DLC (DLC content)
             * cc*.ba2 → CREATION CLUB (only if in active_cc_plugins)
             * Others → CREATION STORE (encrypted, non-extractable)
        
        3. Scan MO2 mods directory recursively (rglob)
           - Each BA2 file is checked against vanilla_ba2_names
           - If filename matches vanilla BA2: REPLACEMENT
           - Otherwise: MOD (new/additional content)
        
        4. Return comprehensive breakdown with metadata
        
        PARAMETERS:
            fo4_path (str): Root directory of Fallout 4 installation
                - Expected: "C:\\Program Files\\Fallout 4"
                - Function will look for: fo4_path/Data/ subdirectory
        
        RETURNS:
            Dict with keys:
            - main: Count of main game BA2s (Fallout4 - *.ba2)
            - dlc: Count of DLC BA2s (DLC*.ba2)
            - creation_club: Count of active CC BA2s (cc*.ba2 in Fallout4.ccc)
            - creation_store: Count of Creation Store BA2s (encrypted)
            - base_game: Sum of main + dlc + creation_club + creation_store
            - mods: Count of non-replacement mod BA2s
            - replacements: Count of mod BA2s replacing vanilla files
            - vanilla_ba2_names: Set of all vanilla BA2 filenames (lowercase)
            - total: base_game + mods + replacements
            - limit: Hard limit of 501 (Fallout 4's safety threshold)
        
        LOGGING:
        Each step logs to ba2-manager.log for debugging:
        - Paths being scanned
        - Active CC plugins found
        - Each BA2 file categorized with explanation
        - Final counts
        
        TROUBLESHOOTING:
        If counts look wrong, check ba2-manager.log for:
        - "Mods path exists: False" → mo2_dir not configured
        - "Fallout4.ccc not found" → fo4_path incorrect
        - "0 BA2 files in mods" → Check rglob is working
        """
        main_count = 0
        main_texture_count = 0
        dlc_count = 0
        dlc_texture_count = 0
        cc_count = 0
        cc_texture_count = 0
        creation_store_count = 0
        creation_store_texture_count = 0
        # Reset to defaults + scanned
        self.vanilla_ba2_names = set(name.lower() for name in self.VANILLA_BA2S)
        
        # Log debug info
        self.logger.info(f"Counting BA2 files from: {fo4_path}")
        self.logger.info(f"MO2 mods directory: {self.mo2_dir}")
        
        # Read active CC plugins from Fallout4.ccc
        active_cc_plugins = self._get_active_cc_plugins(fo4_path)
        
        # Scan base game Data folder
        if fo4_path:
            data_path = Path(fo4_path) / "Data"
            if data_path.exists():
                for ba2_file in data_path.glob("*.ba2"):
                    ba2_name = ba2_file.name.lower()
                    self.vanilla_ba2_names.add(ba2_name)
                    
                    # Categorize BA2 files exactly like PowerShell script
                    if ba2_name.startswith("cc"):
                        # For CC BA2s, only count if plugin is active in Fallout4.ccc
                        ba2_base = ba2_file.stem  # Remove extension
                        # Handle names like "ccbgsfo4119-cyberdog - main.ba2"
                        ba2_base = re.sub(r' - (main|textures)$', '', ba2_base, flags=re.IGNORECASE)
                        
                        if ba2_base.lower() in active_cc_plugins:
                            # Distinguish between main and texture CC BA2s
                            # Texture BA2s contain " - Texture" in the filename
                            if " - texture" in ba2_name:
                                cc_texture_count += 1
                            else:
                                cc_count += 1
                    elif ba2_name.startswith("dlc"):
                        # Distinguish between main and texture DLC BA2s
                        # Texture BA2s contain " - Texture" in the filename
                        if " - texture" in ba2_name:
                            dlc_texture_count += 1
                        else:
                            dlc_count += 1
                    elif ba2_name.startswith("fallout4 - "):
                        # Distinguish between main and texture Fallout4 BA2s
                        # Texture BA2s contain " - Texture" in the filename
                        if " - texture" in ba2_name:
                            main_texture_count += 1
                        else:
                            main_count += 1
                    else:
                        # Creation Store Mods (encrypted, non-extractable)
                        # Distinguish between main and texture Creation Store BA2s
                        if " - texture" in ba2_name:
                            creation_store_texture_count += 1
                        else:
                            creation_store_count += 1
        
        # Count mod BA2s (excluding those that replace vanilla BA2s)
        mod_count = 0
        replacement_count = 0
        
        # Get list of active mods from modlist.txt
        active_mods = self._get_active_mods()
        active_mods_set = {m.lower() for m in active_mods}
        
        # Count mod BA2s separately for MAIN and TEXTURES
        mod_main_count = 0
        mod_texture_count = 0
        replacement_count = 0
        replacement_main_count = 0
        replacement_texture_count = 0
        
        mods_path = Path(self.mo2_dir)
        self.logger.info(f"Scanning mods path: {mods_path}")
        self.logger.info(f"Mods path exists: {mods_path.exists()}")
        
        if mods_path.exists():
            mod_ba2s = list(mods_path.rglob("*.ba2"))
            self.logger.info(f"Found {len(mod_ba2s)} BA2 files in mods")
            
            for ba2_file in mod_ba2s:
                ba2_name = ba2_file.name.lower()
                mod_folder_name = ba2_file.parent.name.lower()
                
                # Only count BA2s from active mods (if active_mods is not empty, check it; if empty, count all)
                if active_mods_set and mod_folder_name not in active_mods_set:
                    self.logger.debug(f"  Skipping BA2 from inactive mod: {ba2_file.relative_to(mods_path)}")
                    continue
                
                self.logger.info(f"  Checking mod BA2: {ba2_file.relative_to(mods_path)}")
                
                if ba2_name in self.vanilla_ba2_names:
                    # Categorize replacement as main or texture
                    if " - textures" in ba2_name:
                        replacement_texture_count += 1
                        self.logger.info(f"    -> Vanilla replacement texture (active)")
                    else:
                        replacement_main_count += 1
                        self.logger.info(f"    -> Vanilla replacement main (active)")
                    replacement_count += 1
                else:
                    # Categorize as MAIN or TEXTURES based on filename pattern
                    # Texture BA2s contain " - Textures" in the filename (e.g., " - Textures.ba2", " - Textures1.ba2")
                    if " - textures" in ba2_name:
                        mod_texture_count += 1
                        self.logger.info(f"    -> Texture BA2 (active)")
                    else:
                        # Treat as main/generic BA2
                        mod_main_count += 1
                        self.logger.info(f"    -> Main BA2 (active)")
        else:
            self.logger.warning(f"Mods directory does not exist: {mods_path}")
        
        base_game_count = main_count + dlc_count + cc_count + creation_store_count
        base_game_texture_count = main_texture_count + dlc_texture_count + cc_texture_count + creation_store_texture_count
        
        self.logger.info(f"Count summary: Base={base_game_count} (Main={main_count}, DLC={dlc_count}, CC={cc_count}, CreationStore={creation_store_count}), BaseTex={base_game_texture_count} (MainTex={main_texture_count}, DLCTex={dlc_texture_count}, CCTex={cc_texture_count}, CreationStoreTex={creation_store_texture_count}), ModMain={mod_main_count}, ModTextures={mod_texture_count}")
        
        return {
            "main": main_count,
            "main_textures": main_texture_count,
            "dlc": dlc_count,
            "dlc_textures": dlc_texture_count,
            "creation_club": cc_count,
            "creation_club_textures": cc_texture_count,
            "creation_store": creation_store_count,
            "creation_store_textures": creation_store_texture_count,
            "base_game": base_game_count,
            "base_game_textures": base_game_texture_count,
            "mod_main": mod_main_count,
            "mod_textures": mod_texture_count,
            "replacements": replacement_count,
            "replacement_main": replacement_main_count,
            "replacement_textures": replacement_texture_count,
            "vanilla_ba2_names": self.vanilla_ba2_names,
            "main_total": base_game_count + mod_main_count,
            "texture_total": base_game_texture_count + mod_texture_count,
            "limit_main": 255,
            "limit_textures": 254
        }
    
    def _get_modlist_path(self, mo2_root: Optional[Path] = None) -> Path:
        """Determine path to modlist.txt"""
        if mo2_root:
            return mo2_root / "profiles" / "Default" / "modlist.txt"
        
        # Try to infer mo2_root from mo2_dir
        mo2_path = Path(self.mo2_dir)
        if mo2_path.name == "mods":
            mo2_root = mo2_path.parent
            return mo2_root / "profiles" / "Default" / "modlist.txt"
        else:
            # mo2_dir is directly in MO2 root or we can't determine it
            return mo2_path.parent / "profiles" / "Default" / "modlist.txt"
    
    def _get_plugins_path(self, mo2_root: Optional[Path] = None) -> Path:
        """Determine path to plugins.txt"""
        if mo2_root:
            return mo2_root / "profiles" / "Default" / "plugins.txt"
        
        # Try to infer mo2_root from mo2_dir
        mo2_path = Path(self.mo2_dir)
        if mo2_path.name == "mods":
            mo2_root = mo2_path.parent
            return mo2_root / "profiles" / "Default" / "plugins.txt"
        else:
            # mo2_dir is directly in MO2 root or we can't determine it
            return mo2_path.parent / "profiles" / "Default" / "plugins.txt"

    def backup_modlist(self) -> bool:
        """Create a backup of modlist.txt on startup"""
        try:
            modlist_path = self._get_modlist_path()
            if not modlist_path.exists():
                self.logger.debug(f"modlist.txt not found at {modlist_path}, skipping backup")
                return False
            
            backup_path = modlist_path.with_suffix('.txt.bak')
            shutil.copy2(modlist_path, backup_path)
            self.logger.info(f"Backed up modlist.txt to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup modlist.txt: {e}")
            return False
    
    def backup_plugins(self) -> bool:
        """Create a backup of plugins.txt on startup"""
        try:
            plugins_path = self._get_plugins_path()
            if not plugins_path.exists():
                self.logger.debug(f"plugins.txt not found at {plugins_path}, skipping backup")
                return False
            
            backup_path = plugins_path.with_suffix('.txt.bak')
            shutil.copy2(plugins_path, backup_path)
            self.logger.info(f"Backed up plugins.txt to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup plugins.txt: {e}")
            return False

    def verify_modlist_integrity(self) -> bool:
        """Verify modlist.txt hasn't changed since backup"""
        try:
            modlist_path = self._get_modlist_path()
            backup_path = modlist_path.with_suffix('.txt.bak')
            
            if not modlist_path.exists() or not backup_path.exists():
                return True # Can't verify
                
            # Simple size/mtime check or full content check?
            # Content check is safer
            import filecmp
            is_same = filecmp.cmp(modlist_path, backup_path, shallow=False)
            if not is_same:
                self.logger.warning("modlist.txt has changed since startup!")
            return is_same
        except Exception as e:
            self.logger.error(f"Failed to verify modlist.txt: {e}")
            return True # Assume okay to avoid blocking user if check fails

    def _get_disabled_plugin_mods(self, mo2_root: Optional[Path] = None) -> set:
        """Read plugins.txt to identify mods with disabled plugins.
        
        Args:
            mo2_root: Optional path to MO2 root directory.
        
        Returns:
            Set of mod folder names that have at least one disabled plugin
        """
        disabled_mods = set()
        plugins_path = self._get_plugins_path(mo2_root)
        
        if not plugins_path.exists():
            self.logger.debug(f"plugins.txt not found at {plugins_path}, no plugin-based filtering")
            return disabled_mods
        
        try:
            with open(plugins_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Disabled plugins are prefixed with *
                    if line.startswith('*'):
                        plugin_name = line[1:].strip()
                        # Extract mod name from plugin by removing extension
                        # Most plugins match their mod folder name (e.g., MyMod.esp -> MyMod/)
                        mod_name = plugin_name.rsplit('.', 1)[0]
                        disabled_mods.add(mod_name)
                        self.logger.debug(f"Found disabled plugin: {plugin_name} (mod: {mod_name})")
                    
            self.logger.info(f"Found {len(disabled_mods)} mods with disabled plugins in plugins.txt")
        except Exception as e:
            self.logger.warning(f"Could not read plugins.txt: {e}")
        
        return disabled_mods
    
    def _get_active_mods(self, mo2_root: Optional[Path] = None) -> List[str]:
        """Read active mods from modlist.txt and filter by plugins.txt.
        
        Args:
            mo2_root: Optional path to MO2 root directory.
        
        Returns:
            List of active mod folder names in MO2 display order (Priority 0 first),
            excluding mods with disabled plugins
        """
        active_mods = []
        modlist_path = self._get_modlist_path(mo2_root)
        
        if not modlist_path.exists():
            self.logger.debug(f"modlist.txt not found at {modlist_path}, counting all mods as active")
            return active_mods
        
        try:
            with open(modlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # modlist.txt is in reverse priority order (Highest priority at top)
            # We want MO2 display order (Priority 0 at top), so we reverse the list
            for line in reversed(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Active mods are prefixed with +
                if line.startswith('+'):
                    mod_name = line[1:].strip()
                    active_mods.append(mod_name)
                    
            self.logger.info(f"Found {len(active_mods)} active mods in modlist.txt")
            
            # Additional filtering: Remove mods with disabled plugins
            disabled_plugin_mods = self._get_disabled_plugin_mods(mo2_root)
            if disabled_plugin_mods:
                original_count = len(active_mods)
                active_mods = [mod for mod in active_mods if mod not in disabled_plugin_mods]
                filtered_count = original_count - len(active_mods)
                if filtered_count > 0:
                    self.logger.info(f"Filtered out {filtered_count} mods with disabled plugins")
                    self.logger.info(f"Final active mod count: {len(active_mods)}")
            
        except Exception as e:
            self.logger.warning(f"Could not read modlist.txt: {e}")
        
        return active_mods
    
    def _get_active_cc_plugins(self, fo4_path: str) -> set[str]:
        """Read active CC plugins from Fallout4.ccc
        
        Args:
            fo4_path: Path to Fallout 4 installation
            
        Returns:
            Set of active CC plugin base names (without extension, lowercased)
        """
        active_cc = set()
        ccc_path = Path(fo4_path) / "Fallout4.ccc"
        
        if ccc_path.exists():
            try:
                with open(ccc_path, 'r') as f:
                    for line in f:
                        trimmed = line.strip()
                        # Match CC plugins: cc*.es[lmp] (case-insensitive)
                        # Allow alphanumeric, hyphens, underscores, and parentheses
                        if re.match(r'^cc.+(\.es[lmp])$', trimmed, re.IGNORECASE):
                            # Remove extension and convert to lowercase for consistent matching
                            plugin_base = re.sub(r'\.[eE][sS][lmp]$', '', trimmed)
                            plugin_base = plugin_base.lower()
                            active_cc.add(plugin_base)
                # Debug: log all active CC plugin names
                self.logger.debug(f"Active CC plugins from Fallout4.ccc: {sorted(active_cc)}")
            except Exception as e:
                self.logger.warning(f"Could not read Fallout4.ccc: {e}")
        
        return active_cc
    
    def get_cc_packages(self, fo4_path: str) -> List[tuple]:
        """
        Get list of all available CC packages and their status.
        Scans Data folder for all CC files, not just active ones.
        
        Args:
            fo4_path: Path to Fallout 4 installation
            
        Returns:
            List of tuples (plugin_id, display_name, is_active)
        """
        packages = []
        if not fo4_path:
            return packages
            
        active_cc = set()
        all_cc_plugins = set()
        
        # 1. Get active plugins from Fallout4.ccc
        active_cc = self._get_active_cc_plugins(fo4_path)
        
        # 2. Scan Data folder for ALL available CC plugins
        data_path = Path(fo4_path) / "Data"
        if data_path.exists():
            for ext in ["*.esl", "*.esm", "*.esp"]:
                for f in data_path.glob(ext):
                    if f.name.lower().startswith("cc"):
                        # Store just the base name without extension for consistent ID
                        base_name = re.sub(r'\.es[lmp]$', '', f.name, flags=re.IGNORECASE).lower()
                        all_cc_plugins.add((base_name, f.name))
        
        # 3. Build package list
        for plugin_base, full_filename in all_cc_plugins:
            is_active = plugin_base in active_cc
            
            # Get display name from dictionary or fallback
            display_name = f"{plugin_base} (Unknown)"
            
            if plugin_base in self.CC_NAMES:
                display_name = self.CC_NAMES[plugin_base]["name"]
            else:
                # Try to find a key that is a prefix of the plugin_base
                for key in self.CC_NAMES:
                    if plugin_base.startswith(key):
                        display_name = self.CC_NAMES[key]["name"]
                        break
            
            # Store full filename as ID so we can write it back to .ccc correctly
            packages.append((full_filename, display_name, is_active))

        return sorted(packages, key=lambda x: x[1])  # Sort by display name
    
    def _get_nexus_url(self, mod_path: Path) -> Optional[str]:
        """
        Extract Nexus URL from meta.ini file in the mod directory.
        """
        meta_file = mod_path / "meta.ini"
        if not meta_file.exists():
            return None
            
        try:
            # Simple INI parsing
            content = meta_file.read_text(encoding='utf-8', errors='ignore')
            
            # Extract required fields
            mod_id_match = re.search(r'^modid=(\d+)', content, re.MULTILINE)
            game_name_match = re.search(r'^gameName=(.+)', content, re.MULTILINE)
            
            if mod_id_match and game_name_match:
                mod_id = mod_id_match.group(1)
                game_name = game_name_match.group(1).lower()
                return f"https://www.nexusmods.com/{game_name}/mods/{mod_id}"
                
        except Exception as e:
            self.logger.warning(f"Error parsing meta.ini in {mod_path}: {e}")
            
        return None

    def list_ba2_mods(self) -> List[BA2Info]:
        """
        List all BA2 mod files with separate tracking of main and texture BA2s.
        
        For each mod, tracks:
        - Whether it has a main BA2 file (not containing " - Texture" in filename)
        - Whether it has a texture BA2 file (containing " - Texture" in filename, e.g. " - Textures.ba2", " - Textures1.ba2")
        - Whether each is currently extracted
        - Total size of all BA2 files
        
        Returns:
            List of BA2Info objects sorted by MO2 load order (Priority 0 first)
        """
        ba2_mods = {}
        mods_path = Path(self.mo2_dir)
        backup_path = Path(self.backup_dir)
        
        # Get list of active mods from modlist.txt
        # This list is in MO2 display order (Priority 0 first)
        active_mods_list = self._get_active_mods()
        
        # Create a set for fast lookups during filtering
        active_mods_set = {m.lower() for m in active_mods_list}
        
        # 1. Scan for BA2 files in mods directory
        if mods_path.exists():
            try:
                for ba2_file in mods_path.rglob("*.ba2"):
                    try:
                        mod_name = ba2_file.parent.name
                        
                        # Skip inactive mods
                        if active_mods_set and mod_name.lower() not in active_mods_set:
                            # self.logger.debug(f"Skipping BA2 from inactive mod: {mod_name}")
                            continue
                        
                        # Skip vanilla replacements (Fallout4-Textures1.ba2, DLCCoast - Textures.ba2, etc.)
                        if ba2_file.name.lower() in self.vanilla_ba2_names:
                            continue
                        
                        # Initialize mod entry if needed
                        if mod_name not in ba2_mods:
                            ba2_mods[mod_name] = {
                                'has_main': False,
                                'has_texture': False,
                                'main_extracted': False,
                                'texture_extracted': False,
                                'total_size': 0,
                                'has_backup': (backup_path / mod_name).exists(),
                                'nexus_url': self._get_nexus_url(ba2_file.parent)
                            }
                        
                        # Categorize BA2 file
                        # Texture BA2s contain " - Texture" in the filename (e.g., " - Textures.ba2", " - Textures1.ba2")
                        is_texture = " - texture" in ba2_file.name.lower()
                        file_size = ba2_file.stat().st_size
                        ba2_mods[mod_name]['total_size'] += file_size
                        
                        if is_texture:
                            ba2_mods[mod_name]['has_texture'] = True
                        else:
                            ba2_mods[mod_name]['has_main'] = True
                            
                    except Exception as e:
                        self.logger.warning(f"Error processing BA2 file {ba2_file}: {e}")
                        continue
            except Exception as e:
                self.logger.error(f"Error listing BA2 mods in {self.mo2_dir}: {e}")
        else:
            self.logger.warning(f"MO2 mods directory not found: {self.mo2_dir}")

        # 2. Check for extracted mods in backup directory
        if backup_path.exists():
            try:
                for mod_backup in backup_path.iterdir():
                    if not mod_backup.is_dir():
                        continue
                        
                    mod_name = mod_backup.name
                    
                    # Skip inactive mods
                    if active_mods_set and mod_name.lower() not in active_mods_set:
                        continue
                        
                    try:
                        # Check what's in the backup
                        main_ba2_in_backup = any(f.name.lower().endswith('.ba2') and " - texture" not in f.name.lower() for f in mod_backup.iterdir())
                        texture_ba2_in_backup = any(" - texture" in f.name.lower() and f.name.lower().endswith('.ba2') for f in mod_backup.iterdir())
                        
                        if not main_ba2_in_backup and not texture_ba2_in_backup:
                            continue
                            
                        # If mod still has BA2 files in live directory, it's partially extracted
                        if mod_name in ba2_mods:
                            self.logger.info(f"  Partially extracted: {mod_name} (has some BA2s live)")
                            # Mark which types are extracted (in backup but not in live)
                            live_data = ba2_mods[mod_name]
                            
                            # Main BA2 is extracted if it's in backup but not live
                            if main_ba2_in_backup and not live_data.get('has_main', False):
                                live_data['main_extracted'] = True
                                live_data['has_main'] = True  # Mod originally had Main BA2
                            
                            # Texture BA2 is extracted if it's in backup but not live
                            if texture_ba2_in_backup and not live_data.get('has_texture', False):
                                live_data['texture_extracted'] = True
                                live_data['has_texture'] = True  # Mod originally had Texture BA2
                            
                            # Mark backup as existing
                            live_data['has_backup'] = True
                            continue
                        
                        # This mod has been fully extracted (no BA2s in live directory)
                        self.logger.info(f"  Fully extracted: {mod_name}")
                        ba2_mods[mod_name] = {
                            'has_main': main_ba2_in_backup,
                            'has_texture': texture_ba2_in_backup,
                            'main_extracted': main_ba2_in_backup,
                            'texture_extracted': texture_ba2_in_backup,
                            'total_size': 0, # Size is 0 in live dir
                            'has_backup': True,
                            'nexus_url': None # Can't easily get URL from backup
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing backup for {mod_name}: {e}")
                        continue
            except Exception as e:
                self.logger.error(f"Error scanning backup directory: {e}")

        # 3. Convert to BA2Info list
        result = []
        for mod_name, data in ba2_mods.items():
            # Only include mods that have at least one BA2 file (main or texture)
            if data['has_main'] or data['has_texture']:
                result.append(BA2Info(
                    mod_name=mod_name,
                    has_main_ba2=data['has_main'],
                    has_texture_ba2=data['has_texture'],
                    main_extracted=data['main_extracted'],
                    texture_extracted=data['texture_extracted'],
                    total_size=data['total_size'],
                    has_backup=data['has_backup'],
                    nexus_url=data['nexus_url']
                ))
        
        # Update tracking file with current mod states
        self._update_mod_tracking(ba2_mods)
        
        # Sort alphabetically by mod name
        result.sort(key=lambda x: x.mod_name.lower())
            
        return result
    
    def create_cc_master_backup(self, fo4_path: str) -> bool:
        """
        Create a master backup of all available CC content found in Data folder.
        This serves as a restore point for "Restore All".
        
        Args:
            fo4_path: Path to Fallout 4 installation
            
        Returns:
            True if successful, False otherwise
        """
        if not fo4_path:
            return False
            
        data_path = Path(fo4_path) / "Data"
        backup_path = Path(fo4_path) / "Creation_Club_Master_Backup.cc_"
        
        # Only create if it doesn't exist
        if backup_path.exists():
            return True
        
        if not data_path.exists():
            self.logger.error(f"Data folder not found: {data_path}")
            return False
            
        try:
            # Find all CC plugins
            cc_plugins = []
            for ext in ["*.esl", "*.esm", "*.esp"]:
                for f in data_path.glob(ext):
                    if f.name.lower().startswith("cc"):
                        cc_plugins.append(f.name)
            
            # Sort for consistency
            cc_plugins.sort(key=str.lower)
            
            # Write to backup file
            with open(backup_path, 'w') as f:
                f.write('\n'.join(cc_plugins))
                
            self.logger.info(f"Created CC master backup with {len(cc_plugins)} plugins: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating CC master backup: {e}")
            return False

    def _reposition_cc_plugins_DISABLED(self, plugins_path: Path, cc_plugins: List[str]) -> bool:
        """
        DISABLED: Alphabetical repositioning conflicts with MO2's behavior.
        Reposition CC plugins in plugins.txt to be alphabetically sorted among
        existing CC content, or after DLC content if no CC exists.
        
        Args:
            plugins_path: Path to plugins.txt file
            cc_plugins: List of CC plugin filenames to reposition (without * prefix)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not plugins_path.exists():
                self.logger.warning(f"plugins.txt not found at {plugins_path}")
                return False
            
            # Read all plugins
            with open(plugins_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
            
            # Separate CC plugins from the list to reposition
            cc_to_add = set(p.lower() for p in cc_plugins)
            
            # Find existing CC and DLC positions
            cc_positions = []  # (index, plugin_name, is_disabled)
            dlc_positions = []
            other_lines = []
            
            for i, line in enumerate(lines):
                stripped = line.lstrip('*').strip()
                if not stripped:
                    continue
                    
                is_disabled = line.startswith('*')
                
                # Check if it's a CC plugin (from Data folder)
                if stripped.lower().startswith('cc') and stripped.lower().endswith(('.esl', '.esm', '.esp')):
                    # Skip if this is one we're repositioning
                    if stripped.lower() not in cc_to_add:
                        cc_positions.append((i, stripped, is_disabled))
                # Check if it's a DLC plugin
                elif stripped.lower().startswith('dlc') and stripped.lower().endswith(('.esl', '.esm', '.esp')):
                    dlc_positions.append((i, stripped, is_disabled))
            
            # Determine insertion point
            if cc_positions:
                # Insert alphabetically among existing CC content
                insert_after = cc_positions[-1][0]  # After last CC plugin
                self.logger.info(f"Inserting CC plugins alphabetically after existing CC content at line {insert_after}")
            elif dlc_positions:
                # Insert after DLC content
                insert_after = dlc_positions[-1][0]
                self.logger.info(f"Inserting CC plugins after DLC content at line {insert_after}")
            else:
                # Insert at the end
                insert_after = len(lines) - 1
                self.logger.info(f"No CC or DLC found, inserting at end")
            
            # Remove lines that contain plugins we're repositioning
            new_lines = []
            for line in lines:
                stripped = line.lstrip('*').strip()
                if stripped.lower() not in cc_to_add:
                    new_lines.append(line)
            
            # Collect all CC plugins (existing + new) for alphabetical sorting
            all_cc = []
            for _, plugin, is_disabled in cc_positions:
                all_cc.append((plugin, is_disabled))
            
            for plugin in cc_plugins:
                # These are being enabled, so not disabled
                all_cc.append((plugin, False))
            
            # Sort alphabetically (case-insensitive)
            all_cc.sort(key=lambda x: x[0].lower())
            
            # Find where to insert in new_lines
            # We need to find the position that corresponds to insert_after
            # Since we removed some lines, recalculate
            actual_insert = 0
            for i, line in enumerate(new_lines):
                stripped = line.lstrip('*').strip()
                if stripped.lower().startswith('dlc') or (stripped.lower().startswith('cc') and stripped.lower() not in cc_to_add):
                    actual_insert = i + 1
            
            # Insert all CC plugins at the calculated position
            for plugin, is_disabled in reversed(all_cc):
                prefix = '*' if is_disabled else ''
                new_lines.insert(actual_insert, f"{prefix}{plugin}")
            
            # Write back to plugins.txt
            with open(plugins_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                if new_lines and not new_lines[-1].endswith('\n'):
                    f.write('\n')
            
            self.logger.info(f"Repositioned {len(cc_plugins)} CC plugins in plugins.txt")
            return True
            
        except Exception as e:
            self.logger.error(f"Error repositioning CC plugins: {e}")
            return False
    
    def _reposition_cc_mods_DISABLED(self, modlist_path: Path, cc_mod_names: List[str]) -> bool:
        """
        DISABLED: Alphabetical repositioning conflicts with MO2's behavior.
        Reposition CC mod entries in modlist.txt to be alphabetically sorted among
        existing CC content, or after official/DLC content if no CC exists.
        
        Args:
            modlist_path: Path to modlist.txt file
            cc_mod_names: List of CC mod folder names to reposition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not modlist_path.exists():
                self.logger.warning(f"modlist.txt not found at {modlist_path}")
                return False
            
            # Read all lines
            with open(modlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
            
            # Separate CC mods to reposition
            cc_to_add = set(m.lower() for m in cc_mod_names)
            
            # Find existing CC and official content positions
            cc_positions = []  # (index, mod_name, is_disabled)
            official_positions = []  # Official/DLC content
            
            for i, line in enumerate(lines):
                stripped = line.lstrip('+-').strip()
                if not stripped or stripped.startswith('#'):
                    continue
                    
                is_disabled = line.startswith('-')
                is_enabled = line.startswith('+')
                
                # Check if it's a CC mod (starts with CC or Creation Club in name)
                # Use case-insensitive matching
                if any(x in stripped.lower() for x in ['creation club', ' cc ', '-cc-', '_cc_', ' (cc)']) or stripped.lower().startswith('cc'):
                    # Skip if this is one we're repositioning
                    if stripped.lower() not in cc_to_add:
                        cc_positions.append((i, stripped, is_disabled))
                # Check for official/DLC content markers
                elif any(x in stripped.lower() for x in ['dlc', 'official', 'bethesda']):
                    official_positions.append((i, stripped, is_disabled))
            
            # Determine insertion point (modlist.txt is in reverse priority order)
            if cc_positions:
                # Insert at the beginning of CC content section
                insert_at = cc_positions[0][0]
                self.logger.info(f"Inserting CC mods alphabetically at beginning of CC section at line {insert_at}")
            elif official_positions:
                # Insert after official content
                insert_at = official_positions[-1][0] + 1
                self.logger.info(f"Inserting CC mods after official content at line {insert_at}")
            else:
                # Insert near the bottom (high priority in MO2)
                insert_at = len(lines)
                self.logger.info(f"No CC or official content found, inserting at end")
            
            # Remove lines that contain mods we're repositioning
            new_lines = []
            for line in lines:
                stripped = line.lstrip('+-').strip()
                if stripped.lower() not in cc_to_add:
                    new_lines.append(line)
            
            # Collect all CC mods (existing + new) for alphabetical sorting
            all_cc = []
            for _, mod_name, is_disabled in cc_positions:
                all_cc.append((mod_name, is_disabled))
            
            for mod_name in cc_mod_names:
                # These are being enabled, so not disabled
                all_cc.append((mod_name, False))
            
            # Sort alphabetically (case-insensitive)
            all_cc.sort(key=lambda x: x[0].lower())
            
            # Recalculate insertion point after removals
            actual_insert = min(insert_at, len(new_lines))
            
            # Insert all CC mods at the calculated position
            for mod_name, is_disabled in reversed(all_cc):
                prefix = '-' if is_disabled else '+'
                new_lines.insert(actual_insert, f"{prefix}{mod_name}")
            
            # Write back to modlist.txt
            with open(modlist_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                if new_lines and not new_lines[-1].endswith('\n'):
                    f.write('\n')
            
            self.logger.info(f"Repositioned {len(cc_mod_names)} CC mods in modlist.txt")
            return True
            
        except Exception as e:
            self.logger.error(f"Error repositioning CC mods in modlist.txt: {e}")
            return False

    def write_ccc_file(self, fo4_path: str, enabled_plugins: List[str]) -> bool:
        """
        Write the Fallout4.ccc file with the provided list of plugins.
        
        Args:
            fo4_path: Path to Fallout 4 installation
            enabled_plugins: List of plugin filenames to include
            
        Returns:
            True if successful, False otherwise
        """
        if not fo4_path:
            return False
            
        ccc_path = Path(fo4_path) / "Fallout4.ccc"
        
        try:
            # Ensure we have a backup first
            self.create_cc_master_backup(fo4_path)
            
            # Write the Fallout4.ccc file
            with open(ccc_path, 'w') as f:
                f.write('\n'.join(enabled_plugins))
                
            self.logger.info(f"Updated Fallout4.ccc with {len(enabled_plugins)} plugins")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing Fallout4.ccc: {e}")
            return False

    def enable_cc_content(self, plugin_base: str, fo4_path: str) -> bool:
        """
        Enable Creation Club content by adding it to Fallout4.ccc
        
        Args:
            plugin_base: Base name of the plugin (e.g., "ccbgsfo4001-pipboy(black)")
            fo4_path: Path to Fallout 4 installation
            
        Returns:
            True if successful, False otherwise
        """
        if not fo4_path:
            self.logger.error("Fallout 4 path not provided")
            return False
            
        ccc_path = Path(fo4_path) / "Fallout4.ccc"
        data_path = Path(fo4_path) / "Data"
        
        # 1. Find the correct filename (with extension)
        plugin_filename = None
        if data_path.exists():
            # Try .esl then .esm then .esp
            for ext in [".esl", ".esm", ".esp", ".ESL", ".ESM", ".ESP"]:
                candidate = data_path / f"{plugin_base}{ext}"
                if candidate.exists():
                    plugin_filename = candidate.name
                    break
        
        if not plugin_filename:
            self.logger.error(f"Could not find plugin file for {plugin_base} in Data folder")
            return False
            
        # 2. Add to Fallout4.ccc if not present
        try:
            lines = []
            if ccc_path.exists():
                with open(ccc_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Check if already present (case-insensitive)
            if any(line.lower() == plugin_filename.lower() for line in lines):
                self.logger.info(f"Plugin {plugin_filename} already active")
                return True
                
            # Append new plugin
            lines.append(plugin_filename)
            
            # Write back
            with open(ccc_path, 'w') as f:
                f.write('\n'.join(lines))
                
            self.logger.info(f"Enabled CC content: {plugin_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling CC content {plugin_base}: {e}")
            return False
    
    def disable_cc_content(self, plugin_base: str, fo4_path: str) -> bool:
        """
        Disable Creation Club content by removing it from Fallout4.ccc
        
        Args:
            plugin_base: Base name of the plugin
            fo4_path: Path to Fallout 4 installation
            
        Returns:
            True if successful, False otherwise
        """
        if not fo4_path:
            self.logger.error("Fallout 4 path not provided")
            return False
            
        ccc_path = Path(fo4_path) / "Fallout4.ccc"
        
        if not ccc_path.exists():
            self.logger.warning("Fallout4.ccc does not exist")
            return True
            
        try:
            with open(ccc_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Filter out the plugin (case-insensitive match on base name)
            # We match "plugin_base.esl" or "plugin_base.esm" or "plugin_base.esp"
            new_lines = []
            removed = False
            
            for line in lines:
                # Check if this line matches the plugin_base (ignoring extension)
                line_base = re.sub(r'\.es[lmp]$', '', line, flags=re.IGNORECASE)
                
                if line_base.lower() == plugin_base.lower():
                    removed = True
                    continue
                new_lines.append(line)
            
            if removed:
                with open(ccc_path, 'w') as f:
                    f.write('\n'.join(new_lines))
                self.logger.info(f"Disabled CC content: {plugin_base}")
            else:
                self.logger.info(f"CC content {plugin_base} was not active")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling CC content {plugin_base}: {e}")
            return False
    
    def get_log_entries(self, lines: int = 50) -> str:
        """Get recent log entries
        
        Args:
            lines: Number of lines to retrieve
            
        Returns:
            Log content as string
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
            return "No log file found"
        except Exception as e:
            return f"Error reading log: {str(e)}"
    
    def extract_mod(self, mod_name: str) -> bool:
        """
        Extract a mod's BA2 files to loose files.
        
        PROCESS:
        1. Create backup of mod folder in backup_dir
        2. Extract all BA2s in the mod folder
        3. Delete original BA2s
        
        Args:
            mod_name: Name of the mod folder
            
        Returns:
            True if successful, False otherwise
        """
        mod_path = Path(self.mo2_dir) / mod_name
        backup_path = Path(self.backup_dir) / mod_name
        
        if not mod_path.exists():
            self.logger.error(f"Mod path not found: {mod_path}")
            return False
            
        if not self.archive2_path or not os.path.exists(self.archive2_path):
            self.logger.error("Archive2.exe not found")
            return False
            
        try:
            # 1. Create Backup (if it doesn't exist, to preserve previous backups)
            if not backup_path.exists():
                self.logger.info(f"Creating backup for {mod_name}...")
                # Ensure backup directory parent exists
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(mod_path, backup_path)
            else:
                self.logger.info(f"Backup already exists for {mod_name}, preserving it")
            
            # 2. Create temp directory for atomic extraction
            import tempfile
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ba2_extract_{mod_name}_"))
            self.logger.debug(f"Using temp directory: {temp_dir}")
            
            # 3. Extract BA2s to temp directory first
            ba2_files = list(mod_path.rglob("*.ba2"))
            if not ba2_files:
                self.logger.warning(f"No BA2 files found in {mod_name}")
                temp_dir.rmdir()  # Clean up temp dir
                return True # Already extracted?
                
            extraction_failed = False
            extracted_ba2s = []
            
            for ba2_file in ba2_files:
                self.logger.info(f"Extracting {ba2_file.name}...")
                # Extract to temp directory for atomic operation
                # Archive2 extracts relative to the output folder
                # If BA2 contains "textures/foo.dds", it will be at "temp_dir/textures/foo.dds"
                
                # Archive2.exe usage: Archive2.exe <archive_path> -extract=<destination_path>
                cmd = f'"{self.archive2_path}" "{ba2_file}" -extract="{temp_dir}"'
                
                # Use startupinfo to hide console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.run(cmd, capture_output=True, startupinfo=startupinfo)
                
                if result.returncode == 0:
                    extracted_ba2s.append(ba2_file)
                else:
                    self.logger.error(f"Failed to extract {ba2_file.name}: {result.stderr.decode()}")
                    extraction_failed = True
                    break
            
            # 4. Handle Failure or Success
            if extraction_failed:
                self.logger.error("Extraction failed. Cleaning up temp directory...")
                # Clean up temp directory
                shutil.rmtree(temp_dir)
                # Original mod folder remains untouched
                return False
            else:
                # Success - Perform atomic swap
                self.logger.info("Extraction successful. Performing atomic swap...")
                
                # Copy all extracted content from temp to mod folder
                for item in temp_dir.iterdir():
                    dest = mod_path / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                
                # Now delete BA2s from mod folder
                self.logger.info("Removing BA2 files from mod folder...")
                for ba2_file in extracted_ba2s:
                    os.remove(ba2_file)
                
                # Clean up temp directory
                shutil.rmtree(temp_dir)
                self.logger.info(f"Extraction complete. Original BA2s backed up to {backup_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error extracting mod {mod_name}: {e}")
            # Clean up temp directory if it exists
            try:
                if 'temp_dir' in locals() and temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except:
                pass
            # Original mod folder should be untouched if extraction failed
            return False

    def restore_mod(self, mod_name: str) -> bool:
        """
        Restore a mod from backup (revert to BA2s).
        
        PROCESS:
        1. Check if backup exists
        2. Delete current mod folder (loose files)
        3. Restore backup folder
        
        Args:
            mod_name: Name of the mod folder
            
        Returns:
            True if successful, False otherwise
        """
        mod_path = Path(self.mo2_dir) / mod_name
        backup_path = Path(self.backup_dir) / mod_name
        
        if not backup_path.exists():
            self.logger.error(f"Backup not found for {mod_name}")
            return False
        
        # Initialize temp path for cleanup in case of error
        temp_path = mod_path.parent / f"_temp_{mod_name}"
            
        try:
            self.logger.info(f"Restoring {mod_name} from backup...")
            
            # 1. Copy backup to temp location first (safer than delete-then-copy)
            if temp_path.exists():
                shutil.rmtree(temp_path)
            shutil.copytree(str(backup_path), str(temp_path))
            self.logger.info(f"Copied backup to temporary location")
            
            # 2. Delete current mod folder only after successful copy
            if mod_path.exists():
                shutil.rmtree(mod_path)
                self.logger.info(f"Deleted current mod folder")
                
            # 3. Move temp folder to final location
            shutil.move(str(temp_path), str(mod_path))
            self.logger.info(f"Moved restored files to mod folder")
            
            # 4. Verify mod folder matches backup before deleting
            # Get all BA2 files in backup
            backup_ba2s = set()
            for ba2_file in backup_path.rglob("*.ba2"):
                backup_ba2s.add(ba2_file.name.lower())
            
            # Get all BA2 files in restored mod folder
            mod_ba2s = set()
            for ba2_file in mod_path.rglob("*.ba2"):
                mod_ba2s.add(ba2_file.name.lower())
            
            # Only delete backup if all BA2s are present
            if backup_ba2s == mod_ba2s:
                shutil.rmtree(str(backup_path))
                self.logger.info(f"Deleted backup folder for {mod_name} (fully restored)")
            else:
                self.logger.warning(f"Backup BA2s don't match restored mod, keeping backup for safety")
            
            self.logger.info(f"Successfully restored {mod_name} from backup")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring mod {mod_name}: {e}")
            # Attempt cleanup of temp folder if it exists
            if temp_path.exists():
                try:
                    shutil.rmtree(temp_path)
                    self.logger.info(f"Cleaned up temporary folder")
                except:
                    pass
            return False

    def extract_mod_ba2(self, mod_name: str, ba2_type: str, create_backup: bool = True) -> bool:
        """
        Extract a specific BA2 file (main or texture) from a mod to loose files.
        
        Args:
            mod_name: Name of the mod folder
            ba2_type: "main" or "texture"
            create_backup: If True, create a backup before extraction (only if needed)
            
        Returns:
            True if successful, False otherwise
        """
        mod_path = Path(self.mo2_dir) / mod_name
        backup_path = Path(self.backup_dir) / mod_name
        
        if not mod_path.exists():
            self.logger.error(f"Mod path not found: {mod_path}")
            return False
            
        if not self.archive2_path or not os.path.exists(self.archive2_path):
            self.logger.error("Archive2.exe not found")
            return False
        
        try:
            # 1. Find BA2 files of the specified type
            ba2_files = []
            for ba2_file in mod_path.rglob("*.ba2"):
                ba2_name = ba2_file.name.lower()
                # Texture BA2s contain " - texture" in the filename (e.g., " - Textures.ba2", " - Textures1.ba2")
                is_texture = " - texture" in ba2_name
                
                if ba2_type == "texture" and is_texture:
                    ba2_files.append(ba2_file)
                elif ba2_type == "main" and not is_texture:
                    ba2_files.append(ba2_file)
            
            if not ba2_files:
                self.logger.warning(f"No {ba2_type} BA2 files found in {mod_name}")
                return True  # Already extracted or doesn't have this type
            
            # 2. Create backup if requested and doesn't exist
            if create_backup and not backup_path.exists():
                self.logger.info(f"Creating backup for {mod_name}...")
                # Ensure backup directory parent exists
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(mod_path, backup_path)
            
            # 3. Extract BA2 files
            for ba2_file in ba2_files:
                self.logger.info(f"Extracting {ba2_file.name}...")
                
                cmd = f'"{self.archive2_path}" "{ba2_file}" -extract="{mod_path}"'
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.run(cmd, capture_output=True, startupinfo=startupinfo)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to extract {ba2_file.name}: {result.stderr.decode()}")
                    return False
            
            # 4. Delete extracted BA2 files
            self.logger.info(f"Removing extracted {ba2_type} BA2 files...")
            for ba2_file in ba2_files:
                os.remove(ba2_file)
            
            self.logger.info(f"Successfully extracted {ba2_type} BA2 for {mod_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting {ba2_type} BA2 for {mod_name}: {e}")
            return False

    def restore_mod_ba2(self, mod_name: str, ba2_type: str) -> bool:
        """
        Restore a specific BA2 file (main or texture) from backup.
        
        If both main and texture BA2s are restored, also remove the backup folder.
        
        Args:
            mod_name: Name of the mod folder
            ba2_type: "main" or "texture"
            
        Returns:
            True if successful, False otherwise
        """
        mod_path = Path(self.mo2_dir) / mod_name
        backup_path = Path(self.backup_dir) / mod_name
        
        if not backup_path.exists():
            self.logger.error(f"Backup not found for {mod_name}")
            return False
        
        try:
            self.logger.info(f"Restoring {ba2_type} BA2 for {mod_name} from backup...")
            
            # Find BA2 files of the specified type in backup
            ba2_files_to_restore = []
            for ba2_file in backup_path.rglob("*.ba2"):
                ba2_name = ba2_file.name.lower()
                # Texture BA2s contain " - texture" in the filename (e.g., " - Textures.ba2", " - Textures1.ba2")
                is_texture = " - texture" in ba2_name
                
                if ba2_type == "texture" and is_texture:
                    ba2_files_to_restore.append(ba2_file)
                elif ba2_type == "main" and not is_texture:
                    ba2_files_to_restore.append(ba2_file)
            
            if not ba2_files_to_restore:
                self.logger.warning(f"No {ba2_type} BA2 files in backup for {mod_name}")
                return True
            
            # Copy BA2 files from backup to mod folder (don't delete from backup)
            for backup_ba2 in ba2_files_to_restore:
                relative_path = backup_ba2.relative_to(backup_path)
                target_ba2 = mod_path / relative_path
                
                # Create parent directory if needed
                target_ba2.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file (keep backup intact)
                shutil.copy2(backup_ba2, target_ba2)
                self.logger.info(f"Restored {backup_ba2.name}")
            
            # Check if mod folder now matches backup (all BA2s restored)
            # Get all BA2 files in backup
            backup_ba2s = set()
            for ba2_file in backup_path.rglob("*.ba2"):
                backup_ba2s.add(ba2_file.name.lower())
            
            # Get all BA2 files in mod folder
            mod_ba2s = set()
            for ba2_file in mod_path.rglob("*.ba2"):
                mod_ba2s.add(ba2_file.name.lower())
            
            # If all BA2s are restored, clean up loose files and delete backup
            if backup_ba2s == mod_ba2s:
                self.logger.info(f"All BA2s restored - cleaning up loose files for {mod_name}")
                
                # Delete all loose files except BA2s, ESPs, and meta.ini
                files_deleted = 0
                for item in mod_path.rglob("*"):
                    if item.is_file():
                        # Keep BA2s, ESPs, ESMs, and meta.ini
                        if item.suffix.lower() not in ['.ba2', '.esp', '.esm'] and item.name.lower() != 'meta.ini':
                            try:
                                item.unlink()
                                files_deleted += 1
                            except Exception as e:
                                self.logger.warning(f"Failed to delete {item.name}: {e}")
                
                # Remove empty directories
                for item in sorted(mod_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                    if item.is_dir() and not any(item.iterdir()):
                        try:
                            item.rmdir()
                        except Exception as e:
                            self.logger.warning(f"Failed to remove empty directory {item.name}: {e}")
                
                self.logger.info(f"Deleted {files_deleted} loose files, mod fully restored to BA2s")
                
                # Now safe to delete backup
                shutil.rmtree(backup_path)
                self.logger.info(f"Deleted backup folder for {mod_name}")
            else:
                missing = backup_ba2s - mod_ba2s
                self.logger.info(f"Mod still missing {len(missing)} BA2(s) from backup, keeping backup and loose files for {mod_name}")
            
            self.logger.info(f"Successfully restored {ba2_type} BA2 for {mod_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring {ba2_type} BA2 for {mod_name}: {e}")
            return False
