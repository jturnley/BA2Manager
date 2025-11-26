"""BA2 file handler for core operations

This module handles all BA2 (Bethesda Archive 2) file operations for Fallout 4.
It provides the core functionality for:

1. COUNTING BA2 FILES
   - Scans Fallout 4 Data directory for base game BA2s
   - Counts mods BA2s from MO2 mods directory (recursively)
   - Categorizes by type: Main, DLC, CC (Creation Club), Creation Store, Mods
   - Tracks vanilla replacements (mod BA2s replacing base game files)
   - Reads Fallout4.ccc to determine which CC content is active
   - MATCHING LOGIC: Exactly replicates Fallout 4 BA2 counting requirements

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
            handler1.setLevel(logging.DEBUG if debug_logging else logging.INFO)
            handler1.setFormatter(formatter)
            self.logger.addHandler(handler1)
        except Exception as e:
            print(f"Warning: Could not set up logging to ba2-manager.log: {e}")
        # Always log to /dist/ba2-manager.log
        try:
            handler2 = logging.FileHandler("dist/ba2-manager.log", mode='a')
            handler2.setLevel(logging.DEBUG if debug_logging else logging.INFO)
            handler2.setFormatter(formatter)
            self.logger.addHandler(handler2)
        except Exception as e:
            print(f"Warning: Could not set up logging to dist/ba2-manager.log: {e}")
        # Always log to console
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG if debug_logging else logging.INFO)
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
        
        THIS IS THE CORE COUNTING LOGIC - Matches Fallout 4 BA2 counting requirements exactly.
        
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
                    
                    # Categorize BA2 files exactly like Fallout 4 requirements
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
                
                # Find the actual mod folder name (first part of relative path from mods directory)
                try:
                    relative_path = ba2_file.relative_to(mods_path)
                    mod_folder_name = relative_path.parts[0].lower()
                except ValueError:
                    # File is not under mods_path, skip
                    continue
                
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
    
    def _get_selected_profile(self, mo2_root: Path) -> str:
        """Read selected_profile from ModOrganizer.ini, returns 'Default' if not found or multiple profiles don't exist"""
        try:
            ini_path = mo2_root / "ModOrganizer.ini"
            if not ini_path.exists():
                self.logger.debug(f"ModOrganizer.ini not found at {ini_path}, using Default profile")
                return "Default"
            
            # Check if multiple profiles exist
            profiles_dir = mo2_root / "profiles"
            if profiles_dir.exists():
                profile_count = sum(1 for p in profiles_dir.iterdir() if p.is_dir())
                if profile_count <= 1:
                    self.logger.debug(f"Only one profile exists, using Default")
                    return "Default"
            
            # Read selected_profile from ini
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_general = False
                for line in f:
                    line = line.strip()
                    if line == "[General]":
                        in_general = True
                        continue
                    elif line.startswith("[") and line.endswith("]"):
                        in_general = False
                        continue
                    
                    if in_general and line.startswith("selected_profile="):
                        value = line.split("=", 1)[1].strip()
                        if value.startswith("@ByteArray(") and value.endswith(")"):
                            if len(value) > 12:
                                profile_name = value[11:-1]
                                self.logger.debug(f"Selected profile from ModOrganizer.ini: {profile_name}")
                                return profile_name
                        else:
                            self.logger.debug(f"Selected profile from ModOrganizer.ini: {value}")
                            return value
        except Exception as e:
            self.logger.warning(f"Error reading selected_profile from ModOrganizer.ini: {e}")
        
        self.logger.debug("Using Default profile as fallback")
        return "Default"
    
    def _get_modlist_path(self, mo2_root: Optional[Path] = None) -> Path:
        """Determine path to modlist.txt using selected profile if multiple profiles exist"""
        if mo2_root:
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "modlist.txt"
        
        # Try to infer mo2_root from mo2_dir
        mo2_path = Path(self.mo2_dir)
        if mo2_path.name == "mods":
            mo2_root = mo2_path.parent
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "modlist.txt"
        else:
            # mo2_dir is directly in MO2 root or we can't determine it
            mo2_root = mo2_path.parent
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "modlist.txt"
    
    def _get_plugins_path(self, mo2_root: Optional[Path] = None) -> Path:
        """Determine path to plugins.txt using selected profile if multiple profiles exist"""
        if mo2_root:
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "plugins.txt"
        
        # Try to infer mo2_root from mo2_dir
        mo2_path = Path(self.mo2_dir)
        if mo2_path.name == "mods":
            mo2_root = mo2_path.parent
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "plugins.txt"
        else:
            # mo2_dir is directly in MO2 root or we can't determine it
            mo2_root = mo2_path.parent
            profile_name = self._get_selected_profile(mo2_root)
            return mo2_root / "profiles" / profile_name / "plugins.txt"

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
    
    def _register_mo2_mod(self, mod_name: str, plugin_name: str) -> bool:
        """Register a new mod in MO2's modlist.txt and plugins.txt
        
        Args:
            mod_name: Name of the mod folder
            plugin_name: Name of the plugin file (e.g., "CCMerged.esl")
            
        Returns:
            True if registration succeeded, False otherwise
        """
        try:
            # Add to modlist.txt (at the top, so it's Priority 0)
            modlist_path = self._get_modlist_path()
            if modlist_path.exists():
                with open(modlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Check if already in list
                mod_entry = f"+{mod_name}\n"
                if mod_entry not in lines:
                    # Add at top (end of file since file is in reverse priority order)
                    lines.append(mod_entry)
                    
                    with open(modlist_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    self.logger.info(f"Added {mod_name} to modlist.txt")
                else:
                    self.logger.debug(f"{mod_name} already in modlist.txt")
            
            # Add to plugins.txt (active plugin)
            plugins_path = self._get_plugins_path()
            if plugins_path.exists():
                with open(plugins_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Check if already in list (either enabled or disabled)
                plugin_entry = f"*{plugin_name}\n"
                plugin_entry_enabled = f"{plugin_name}\n"
                
                if plugin_entry not in lines and plugin_entry_enabled not in lines:
                    # Add as enabled plugin (no * prefix)
                    lines.append(plugin_entry_enabled)
                    
                    with open(plugins_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    self.logger.info(f"Added {plugin_name} to plugins.txt (enabled)")
                else:
                    self.logger.debug(f"{plugin_name} already in plugins.txt")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to register mod in MO2 lists: {e}")
            return False
    
    def _unregister_mo2_mod(self, mod_name: str, plugin_name: str) -> bool:
        """Remove a mod from MO2's modlist.txt and plugins.txt
        
        Args:
            mod_name: Name of the mod folder
            plugin_name: Name of the plugin file (e.g., "CCMerged.esl")
            
        Returns:
            True if unregistration succeeded, False otherwise
        """
        try:
            # Remove from modlist.txt
            modlist_path = self._get_modlist_path()
            if modlist_path.exists():
                with open(modlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Remove all entries for this mod (both +ModName and -ModName)
                mod_entries = [f"+{mod_name}\n", f"-{mod_name}\n"]
                lines = [line for line in lines if line not in mod_entries]
                
                with open(modlist_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                self.logger.info(f"Removed {mod_name} from modlist.txt")
            
            # Remove from plugins.txt
            plugins_path = self._get_plugins_path()
            if plugins_path.exists():
                with open(plugins_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Remove both enabled and disabled entries
                plugin_entries = [f"*{plugin_name}\n", f"{plugin_name}\n"]
                lines = [line for line in lines if line not in plugin_entries]
                
                with open(plugins_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                self.logger.info(f"Removed {plugin_name} from plugins.txt")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to unregister mod from MO2 lists: {e}")
            return False

    def _get_disabled_plugin_mods(self, mo2_root: Optional[Path] = None) -> set[str]:
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
                        try:
                            file_size = ba2_file.stat().st_size
                        except (FileNotFoundError, PermissionError) as e:
                            self.logger.warning(f"Cannot access {ba2_file.name}: {e}")
                            continue
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
                        # Get all BA2 files in backup once
                        backup_ba2_files = [f for f in mod_backup.iterdir() if f.name.lower().endswith('.ba2')]
                        
                        # Check what types are in backup
                        main_ba2_in_backup = any(" - texture" not in f.name.lower() for f in backup_ba2_files)
                        texture_ba2_in_backup = any(" - texture" in f.name.lower() for f in backup_ba2_files)
                        
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
                
                result = subprocess.run(cmd, capture_output=True, startupinfo=startupinfo, timeout=300)
                
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
                
                result = subprocess.run(cmd, capture_output=True, startupinfo=startupinfo, timeout=300)
                
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
    
    def merge_cc_ba2s(self, fo4_path: str, output_name: str = "CCMerged") -> Dict[str, Any]:
        """
        Merge all Creation Club BA2 files into two merged archives.
        
        This reduces BA2 count by combining all CC archives into:
        - <output_name> - Main.ba2 (all non-texture files)
        - <output_name> - Textures.ba2 (all texture files)
        
        The merged files are placed in a new mod folder in MO2's mods directory
        and automatically registered as an active mod.
        
        Args:
            fo4_path: Path to Fallout 4 installation
            output_name: Base name for merged archives (default: "CCMerged")
            
        Returns:
            Dict with:
                - success: bool
                - merged_main: path to merged main BA2 (if created)
                - merged_textures: path to merged texture BA2 (if created)
                - original_count: number of CC BA2s merged
                - backup_path: path to backup folder
                - mod_folder: path to created MO2 mod folder
                - error: error message (if failed)
        """
        if not self.archive2_path or not Path(self.archive2_path).exists():
            return {"success": False, "error": "Archive2.exe not found"}
        
        data_path = Path(fo4_path) / "Data"
        if not data_path.exists():
            return {"success": False, "error": "Fallout 4 Data folder not found"}
        
        # Create mod folder in MO2 mods directory
        mods_path = Path(self.mo2_dir)
        mod_folder = mods_path / output_name
        if mod_folder.exists():
            self.logger.warning(f"Mod folder {output_name} already exists, removing it")
            shutil.rmtree(mod_folder)
        mod_folder.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Created MO2 mod folder: {mod_folder}")
        
        # Create backup directory for original CC BA2s
        backup_root = Path(self.backup_dir) / "CC_Merge_Backup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_root / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create temp working directory
        temp_path = Path(self.backup_dir) / "CC_Merge_Temp"
        if temp_path.exists():
            shutil.rmtree(temp_path)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        general_path = temp_path / "General"
        textures_path = temp_path / "Textures"
        general_path.mkdir(exist_ok=True)
        textures_path.mkdir(exist_ok=True)
        
        try:
            self.logger.info("Starting CC BA2 merge process...")
            self.logger.info("="*60)
            
            # 1. Find all CC BA2 files
            cc_ba2_files = []
            for ba2_file in data_path.glob("cc*.ba2"):
                cc_ba2_files.append(ba2_file)
            
            if not cc_ba2_files:
                return {"success": False, "error": "No CC BA2 files found to merge"}
            
            # Sort CC BA2s by load order (alphabetical for CC content)
            # CC mods don't appear in modlist.txt, so alphabetical order is correct
            cc_ba2_files.sort(key=lambda x: x.name.lower())
            
            self.logger.info(f"Found {len(cc_ba2_files)} CC BA2 files to merge (sorted by load order)")
            
            # DEBUG: Log pre-merge statistics
            if self.logger.level <= 10:  # DEBUG level
                total_original_size = sum(f.stat().st_size for f in cc_ba2_files)
                self.logger.debug(f"Total original size: {total_original_size / (1024**2):.2f} MB")
                self.logger.debug("First 10 BA2s by load order:")
                for i, ba2 in enumerate(cc_ba2_files[:10], 1):
                    size_mb = ba2.stat().st_size / (1024**2)
                    self.logger.debug(f"  {i}. {ba2.name} ({size_mb:.2f} MB)")
                if len(cc_ba2_files) > 10:
                    self.logger.debug(f"  ... and {len(cc_ba2_files) - 10} more")
            
            # 2. Backup original BA2 files
            for ba2_file in cc_ba2_files:
                shutil.copy2(ba2_file, backup_path / ba2_file.name)
            self.logger.info(f"Backed up {len(cc_ba2_files)} CC BA2 files to {backup_path}")
            
            # 3. Extract all CC BA2s to temp folders (separated by type)
            # Files with same paths will overwrite - last one wins (load order priority)
            # CC BA2s are already sorted by load order (alphabetical)
            general_ba2s = []
            texture_ba2s = []
            
            # Track file overwrites for diagnostics
            overwrite_tracker = {}  # path -> list of BA2 names that provided it
            
            for ba2_idx, ba2_file in enumerate(cc_ba2_files, 1):
                ba2_name = ba2_file.name.lower()
                # Check for both singular and plural texture naming
                is_texture = " - texture" in ba2_name or " - textures" in ba2_name
                
                if is_texture:
                    texture_ba2s.append(ba2_file)
                    # Extract directly to textures_path - files will overwrite if duplicate
                    extract_to = textures_path
                else:
                    general_ba2s.append(ba2_file)
                    # Extract directly to general_path - files will overwrite if duplicate
                    extract_to = general_path
                
                # Count files before extraction (for overwrite detection)
                files_before = set(str(f.relative_to(extract_to)) for f in extract_to.rglob("*") if f.is_file())
                
                # Extract BA2 (files merge/overwrite at same level)
                self.logger.info(f"[{ba2_idx}/{len(cc_ba2_files)}] Extracting {ba2_file.name} to {extract_to.name}/...")
                
                import time
                extract_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(ba2_file), f"-e={extract_to}"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                extract_time = time.time() - extract_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to extract {ba2_file.name}: {result.stderr}")
                
                # Count files after extraction
                files_after = set(str(f.relative_to(extract_to)) for f in extract_to.rglob("*") if f.is_file())
                new_files = files_after - files_before
                overwritten_files = files_before & files_after
                
                self.logger.debug(f"  Extracted {len(new_files)} new files, {len(overwritten_files)} overwrites in {extract_time:.1f}s")
                
                # Track which BA2s provide each file (for deduplication analysis)
                if self.logger.level <= 10:  # DEBUG level
                    for file_path in new_files:
                        if file_path not in overwrite_tracker:
                            overwrite_tracker[file_path] = []
                        overwrite_tracker[file_path].append(ba2_file.name)
                
                # Log extraction output if verbose
                if result.stdout:
                    self.logger.debug(f"  Archive2 output: {result.stdout.strip()}")
            
            self.logger.info(f"Extracted {len(general_ba2s)} general and {len(texture_ba2s)} texture BA2s")
            
            # Count unique files after extraction (accounting for overwrites)
            general_file_count = sum(1 for _ in general_path.rglob("*") if _.is_file())
            texture_file_count = sum(1 for _ in textures_path.rglob("*") if _.is_file())
            self.logger.info(f"Total unique files: {general_file_count} general, {texture_file_count} textures")
            
            # DEBUG: Deduplication analysis
            if self.logger.level <= 10 and overwrite_tracker:
                duplicates = {path: ba2s for path, ba2s in overwrite_tracker.items() if len(ba2s) > 1}
                if duplicates:
                    self.logger.debug(f"Deduplication: {len(duplicates)} files appeared in multiple BA2s")
                    # Show most duplicated files
                    top_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:5]
                    self.logger.debug("Most overwritten files:")
                    for path, ba2s in top_dupes:
                        self.logger.debug(f"  {path}: in {len(ba2s)} BA2s (winner: {ba2s[-1]})")
                else:
                    self.logger.debug("No duplicate files detected - all files unique")
            
            # 4. Separate Sounds
            sounds_dir = temp_path / "Sounds"
            sounds_dir.mkdir()
            sound_extensions = {".xwm", ".wav", ".fuz"}
            has_sounds = False
            
            for f in general_path.rglob("*"):
                if f.is_file() and f.suffix.lower() in sound_extensions:
                    rel = f.relative_to(general_path)
                    dest = sounds_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dest))
                    has_sounds = True
            
            if has_sounds:
                sound_file_count = sum(1 for _ in sounds_dir.rglob("*") if _.is_file())
                self.logger.info(f"Separated {sound_file_count} sound files to separate archive")
            
            # 5. Create merged archives
            merged_main_path = None
            merged_sounds_path = None
            merged_texture_paths = []
            general_file_count = 0
            texture_file_count = 0
            original_main_size = 0
            original_texture_size = 0
            
            # Calculate original sizes
            for ba2_file in general_ba2s:
                original_main_size += ba2_file.stat().st_size
            for ba2_file in texture_ba2s:
                original_texture_size += ba2_file.stat().st_size
            
            # Pack General BA2
            if general_ba2s:
                merged_main_path = mod_folder / f"{output_name} - Main.ba2"
                self.logger.info(f"Creating merged main BA2: {merged_main_path.name}")
                
                # Get all files once for counting and size calculation
                general_files = list(general_path.rglob("*"))
                general_files = [f for f in general_files if f.is_file()]
                general_file_count = len(general_files)
                uncompressed_size = sum(f.stat().st_size for f in general_files)
                self.logger.info(f"Packing {general_file_count} files, {uncompressed_size / (1024**2):.2f} MB uncompressed")
                
                # Create source file list
                source_list = temp_path / "general_files.txt"
                with open(source_list, 'w') as f:
                    for item in general_files:
                        # Write relative path from general_path
                        rel_path = item.relative_to(general_path)
                        f.write(f"{rel_path}\n")
                
                import time
                pack_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(general_path), 
                     f"-c={merged_main_path}", 
                     "-f=General",
                     f"-r={general_path}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                pack_time = time.time() - pack_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to create merged main BA2: {result.stderr}")
                
                merged_size = merged_main_path.stat().st_size
                compression_ratio = (1 - merged_size / uncompressed_size) * 100 if uncompressed_size > 0 else 0
                self.logger.info(f"Created {merged_main_path.name} in {pack_time:.1f}s")
                self.logger.info(f"  Final: {merged_size / 1024 / 1024:.1f} MB, {general_file_count} files")
                self.logger.info(f"  Compression: {uncompressed_size / (1024**2):.1f} MB → {merged_size / 1024 / 1024:.1f} MB ({compression_ratio:.1f}%)")
                self.logger.info(f"  Original {len(general_ba2s)} BA2s: {original_main_size / 1024 / 1024:.1f} MB")
                self.logger.info(f"  Space saved: {(original_main_size - merged_size) / 1024 / 1024:.1f} MB ({((original_main_size - merged_size) / original_main_size * 100):.1f}%)")
            
            # Pack Sounds BA2 (Uncompressed)
            if has_sounds:
                merged_sounds_path = mod_folder / f"{output_name} - Sounds.ba2"
                sound_file_count = sum(1 for _ in sounds_dir.rglob("*") if _.is_file())
                uncompressed_size = sum(f.stat().st_size for f in sounds_dir.rglob("*") if f.is_file())
                self.logger.info(f"Creating {merged_sounds_path.name} ({sound_file_count} files, {uncompressed_size / (1024**2):.2f} MB uncompressed)...")
                
                import time
                pack_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(sounds_dir), 
                     f"-c={merged_sounds_path}", 
                     "-f=General",
                     "-compression=None",
                     f"-r={sounds_dir}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                pack_time = time.time() - pack_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to create merged sounds BA2: {result.stderr}")
                
                merged_size = merged_sounds_path.stat().st_size
                self.logger.info(f"Created {merged_sounds_path.name} (uncompressed) in {pack_time:.1f}s")
                self.logger.info(f"  Final: {merged_size / 1024 / 1024:.1f} MB, {sound_file_count} files")
            
            # Pack Textures BA2 (with 3GB split logic)
            if texture_ba2s:
                # Get all texture files once
                texture_files = [(item, item.stat().st_size) for item in textures_path.rglob("*") if item.is_file()]
                texture_file_count = len(texture_files)
                
                # Sort by size (descending) to optimize packing, or keep path order?
                # Path order is safer for related textures, but size sorting helps bin packing.
                # Let's stick to path order (default) but just iterate.
                # Actually, simple accumulation is fine.
                
                # 3GB limit (approx 3.5GB max safe limit, using 3GB to be safe)
                MAX_BA2_SIZE = 3 * 1024 * 1024 * 1024
                
                archive_groups = []
                current_group = []
                current_size = 0
                
                for file_path, file_size in texture_files:
                    # If adding this file exceeds limit, start new group
                    # (Only if current group is not empty - single huge file must go somewhere)
                    if current_size + file_size > MAX_BA2_SIZE and current_group:
                        archive_groups.append(current_group)
                        current_group = []
                        current_size = 0
                    
                    current_group.append(file_path)
                    current_size += file_size
                
                if current_group:
                    archive_groups.append(current_group)
                
                total_uncompressed = sum(size for _, size in texture_files)
                self.logger.info(f"Total uncompressed texture data: {total_uncompressed / (1024**3):.2f}GB")
                
                if len(archive_groups) > 1:
                    self.logger.info(f"Splitting textures into {len(archive_groups)} archives (exceeded 3GB limit)")
                
                import time
                
                for idx, file_group in enumerate(archive_groups):
                    # Naming: 
                    # Index 0: CCMerged - Textures.ba2 (and CCMerged.esl)
                    # Index 1: CCMerged_Part2 - Textures.ba2 (and CCMerged_Part2.esl)
                    # Index 2: CCMerged_Part3 - Textures.ba2 (and CCMerged_Part3.esl)
                    
                    suffix = "" if idx == 0 else f"_Part{idx + 1}"
                    archive_name = f"{output_name}{suffix} - Textures.ba2"
                    merged_textures_path = mod_folder / archive_name
                    
                    group_uncompressed = sum(f.stat().st_size for f in file_group)
                    self.logger.info(f"Creating {archive_name} with {len(file_group)} files ({group_uncompressed / (1024**3):.2f}GB uncompressed)...")
                    
                    # Create temp folder for this group
                    split_temp = temp_path / f"textures_split_{idx}"
                    if split_temp.exists():
                        shutil.rmtree(split_temp)
                    split_temp.mkdir(exist_ok=True)
                    
                    # Copy files to temp folder (preserving structure)
                    for file_path in file_group:
                        rel_path = file_path.relative_to(textures_path)
                        dest_path = split_temp / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                    
                    pack_start = time.time()
                    result = subprocess.run(
                        [self.archive2_path, str(split_temp), 
                         f"-c={merged_textures_path}", 
                         "-f=DDS",
                         f"-r={split_temp}"],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    pack_time = time.time() - pack_start
                    
                    if result.returncode != 0:
                        raise Exception(f"Failed to create {archive_name}: {result.stderr}")
                    
                    merged_size = merged_textures_path.stat().st_size
                    compression_ratio = (1 - merged_size / group_uncompressed) * 100 if group_uncompressed > 0 else 0
                    merged_texture_paths.append(merged_textures_path)
                    
                    self.logger.info(f"  Created {archive_name}: {merged_size / 1024 / 1024:.1f} MB in {pack_time:.1f}s")
                    self.logger.info(f"    Compression: {compression_ratio:.1f}%")
                    
                    # Create corresponding ESL if this is a split part (Part2+)
                    # The main ESL (CCMerged.esl) is created later in step 6
                    if idx > 0:
                        part_esl_name = f"{output_name}{suffix}.esl"
                        part_esl_path = mod_folder / part_esl_name
                        self._create_dummy_esl(part_esl_path)
                        self._register_mo2_mod(output_name, part_esl_name)
                        self.logger.info(f"  Created and registered {part_esl_name}")
                
                # Log total texture results
                total_merged_texture_size = sum(p.stat().st_size for p in merged_texture_paths)
                self.logger.info(f"Total texture archives: {len(merged_texture_paths)}, {total_merged_texture_size / 1024 / 1024:.1f} MB")
                self.logger.info(f"  Original {len(texture_ba2s)} BA2s: {original_texture_size / 1024 / 1024:.1f} MB")
                self.logger.info(f"  Space saved: {(original_texture_size - total_merged_texture_size) / 1024 / 1024:.1f} MB ({((original_texture_size - total_merged_texture_size) / original_texture_size * 100):.1f}%)")
            
            # 5. Delete original CC BA2 files
            for ba2_file in cc_ba2_files:
                ba2_file.unlink()
            self.logger.info(f"Removed {len(cc_ba2_files)} original CC BA2 files")
            
            # 6. Create dummy ESLs to load merged BA2s
            created_esls = []
            dummy_esl = mod_folder / f"{output_name}.esl"
            self._create_dummy_esl(dummy_esl)
            created_esls.append(dummy_esl.name)
            self.logger.info(f"Created dummy ESL: {dummy_esl.name}")
            
            # Create dummy ESL for sounds if they exist
            if has_sounds:
                sounds_esl = mod_folder / f"{output_name}_Sounds.esl"
                self._create_dummy_esl(sounds_esl)
                created_esls.append(sounds_esl.name)
                self.logger.info(f"Created dummy ESL for sounds: {sounds_esl.name}")
            
            # 7. Register mod in MO2 mod and plugin lists
            self._register_mo2_mod(output_name, created_esls[0])
            
            # 8. Clean up temp directory
            shutil.rmtree(temp_path)
            
            # Summary statistics
            self.logger.info("="*60)
            self.logger.info("CC BA2 MERGE SUMMARY:")
            self.logger.info(f"  Original: {len(cc_ba2_files)} CC BA2 files")
            merged_count = 1 if merged_main_path else 0
            merged_count += len(merged_texture_paths) if texture_ba2s else 0
            merged_count += 1 if has_sounds else 0
            self.logger.info(f"  Merged: {merged_count} BA2 file(s) (Main, Textures, Sounds)")
            self.logger.info(f"  Reduction: {len(cc_ba2_files)} → {merged_count} ({(1 - merged_count/len(cc_ba2_files))*100:.1f}% fewer files)")
            
            total_original = original_main_size + original_texture_size
            total_merged = (merged_main_path.stat().st_size if merged_main_path else 0)
            total_merged += sum(p.stat().st_size for p in merged_texture_paths) if merged_texture_paths else 0
            total_merged += (merged_sounds_path.stat().st_size if merged_sounds_path else 0)
            self.logger.info(f"  Total space: {total_original / (1024**2):.1f} MB → {total_merged / (1024**2):.1f} MB")
            self.logger.info(f"  Space saved: {(total_original - total_merged) / (1024**2):.1f} MB ({((total_original - total_merged)/total_original*100):.1f}%)")
            self.logger.info(f"  Backup: {backup_path}")
            self.logger.info(f"  Mod folder: {mod_folder}")
            self.logger.info("="*60)
            self.logger.info("CC BA2 merge completed successfully!")
            
            return {
                "success": True,
                "merged_main": str(merged_main_path) if merged_main_path else None,
                "merged_textures": [str(p) for p in merged_texture_paths] if texture_ba2s else [],
                "texture_archive_count": len(merged_texture_paths) if texture_ba2s else 0,
                "original_count": len(cc_ba2_files),
                "backup_path": str(backup_path),
                "dummy_esl": str(dummy_esl),
                "mod_folder": str(mod_folder)
            }
            
        except Exception as e:
            self.logger.error(f"Error merging CC BA2s: {e}")
            # Clean up temp directory on error
            if temp_path.exists():
                shutil.rmtree(temp_path)
            return {"success": False, "error": str(e)}
    
    def merge_custom_ba2s(self, mod_names: list, fo4_path: str, output_name: str) -> Dict[str, Any]:
        """
        Merge specified mods' BA2 files into unified archives.
        
        Similar to merge_cc_ba2s but works with any list of mod names.
        
        Args:
            mod_names: List of mod names to merge
            fo4_path: Path to Fallout 4 installation
            output_name: Base name for merged archives
            
        Returns:
            Dict with success, merged paths, backup path, etc.
        """
        if not self.archive2_path or not Path(self.archive2_path).exists():
            return {"success": False, "error": "Archive2.exe not found"}
        
        data_path = Path(fo4_path) / "Data"
        if not data_path.exists():
            return {"success": False, "error": "Fallout 4 Data folder not found"}
        
        # Get BA2 files for selected mods
        all_ba2s = []
        for mod_name in mod_names:
            ba2_files = list(data_path.glob(f"{mod_name}*.ba2"))
            if ba2_files:
                all_ba2s.extend(ba2_files)
        
        if not all_ba2s:
            return {"success": False, "error": "No BA2 files found for selected mods"}
        
        # Create backup directory
        backup_root = Path(self.backup_dir) / "Custom_Merge_Backup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_root / f"{output_name}_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create temp working directory
        temp_path = Path(self.backup_dir) / "Custom_Merge_Temp"
        if temp_path.exists():
            shutil.rmtree(temp_path)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        general_path = temp_path / "General"
        textures_path = temp_path / "Textures"
        general_path.mkdir(exist_ok=True)
        textures_path.mkdir(exist_ok=True)
        
        try:
            self.logger.info(f"Starting custom mod merge: {output_name}")
            self.logger.info("="*60)
            self.logger.info(f"Merging {len(all_ba2s)} BA2 files from {len(mod_names)} mods")
            
            # DEBUG: Log selected mods
            if self.logger.level <= 10:
                self.logger.debug("Selected mods:")
                for i, mod in enumerate(mod_names, 1):
                    mod_ba2s = [f for f in all_ba2s if f.stem.lower().startswith(mod.lower())]
                    total_size = sum(f.stat().st_size for f in mod_ba2s)
                    self.logger.debug(f"  {i}. {mod} ({len(mod_ba2s)} BA2s, {total_size / (1024**2):.2f} MB)")
            
            # Get load order from modlist.txt to ensure correct overwrite priority
            active_mods = self._get_active_mods()
            load_order = {mod.lower(): idx for idx, mod in enumerate(active_mods)}
            
            # Sort BA2s by load order (lower index = earlier load, will be overwritten by later)
            def get_load_priority(ba2_file):
                # Extract mod name from BA2 filename by removing BA2 suffix patterns
                ba2_name = ba2_file.stem  # Get filename without .ba2 extension
                # Remove common suffixes like " - Main", " - Textures", etc.
                for suffix in [' - main', ' - textures', ' - texture', '-main', '-textures', '-texture']:
                    if ba2_name.lower().endswith(suffix):
                        ba2_name = ba2_name[:-len(suffix)]
                        break
                mod_name = ba2_name.lower()
                # Return load order index, or high number if not in modlist
                priority = load_order.get(mod_name, 999999)
                self.logger.debug(f"BA2 {ba2_file.name} -> mod '{mod_name}' -> priority {priority}")
                return priority
            
            all_ba2s.sort(key=get_load_priority)
            self.logger.info(f"Sorted {len(all_ba2s)} BA2s by modlist.txt load order")
            
            # DEBUG: Show final load order
            if self.logger.level <= 10:
                self.logger.debug("Load order (first 10):")
                for i, ba2 in enumerate(all_ba2s[:10], 1):
                    size_mb = ba2.stat().st_size / (1024**2)
                    self.logger.debug(f"  {i}. {ba2.name} ({size_mb:.2f} MB)")
                if len(all_ba2s) > 10:
                    self.logger.debug(f"  ... and {len(all_ba2s) - 10} more")
            
            # Backup original BA2 files
            for ba2_file in all_ba2s:
                shutil.copy2(ba2_file, backup_path / ba2_file.name)
            self.logger.info(f"Backed up {len(all_ba2s)} BA2 files to {backup_path}")
            
            # Separate into main and texture archives (preserving load order)
            main_ba2s = [f for f in all_ba2s if 'texture' not in f.name.lower()]
            texture_ba2s = [f for f in all_ba2s if 'texture' in f.name.lower()]
            
            self.logger.info(f"Found {len(main_ba2s)} main BA2s and {len(texture_ba2s)} texture BA2s")
            
            # Extract all main BA2s (in load order - earlier mods extracted first, later overwrites)
            original_main_size = 0
            import time
            for ba2_idx, ba2_file in enumerate(main_ba2s, 1):
                self.logger.info(f"[{ba2_idx}/{len(main_ba2s)}] Extracting {ba2_file.name} (load order maintained)...")
                original_main_size += ba2_file.stat().st_size
                
                files_before = sum(1 for _ in general_path.rglob("*") if _.is_file())
                extract_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(ba2_file), f"-e={general_path}"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                extract_time = time.time() - extract_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to extract {ba2_file.name}: {result.stderr}")
                
                files_after = sum(1 for _ in general_path.rglob("*") if _.is_file())
                new_files = files_after - files_before
                self.logger.debug(f"  Extracted {new_files} files in {extract_time:.1f}s (total now: {files_after})")
            
            # Extract all texture BA2s
            original_texture_size = 0
            for ba2_idx, ba2_file in enumerate(texture_ba2s, 1):
                self.logger.info(f"[{ba2_idx}/{len(texture_ba2s)}] Extracting {ba2_file.name}...")
                original_texture_size += ba2_file.stat().st_size
                
                files_before = sum(1 for _ in textures_path.rglob("*") if _.is_file())
                extract_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(ba2_file), f"-e={textures_path}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                extract_time = time.time() - extract_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to extract {ba2_file.name}: {result.stderr}")
                
                files_after = sum(1 for _ in textures_path.rglob("*") if _.is_file())
                new_files = files_after - files_before
                self.logger.debug(f"  Extracted {new_files} files in {extract_time:.1f}s (total now: {files_after})")
            
            # Separate Sounds
            sounds_dir = temp_path / "Sounds"
            sounds_dir.mkdir()
            sound_extensions = {".xwm", ".wav", ".fuz"}
            has_sounds = False
            
            for f in general_path.rglob("*"):
                if f.is_file() and f.suffix.lower() in sound_extensions:
                    rel = f.relative_to(general_path)
                    dest = sounds_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dest))
                    has_sounds = True
            
            if has_sounds:
                sound_file_count = sum(1 for _ in sounds_dir.rglob("*") if _.is_file())
                self.logger.info(f"Separated {sound_file_count} sound files to separate archive")
            
            # Pack main BA2
            merged_main_path = None
            merged_sounds_path = None
            merged_texture_paths = []
            if main_ba2s:
                merged_main_path = data_path / f"{output_name} - Main.ba2"
                file_count = sum(1 for _ in general_path.rglob("*") if _.is_file())
                uncompressed_size = sum(f.stat().st_size for f in general_path.rglob("*") if f.is_file())
                self.logger.info(f"Creating {merged_main_path.name} ({file_count} files, {uncompressed_size / (1024**2):.2f} MB uncompressed)...")
                
                import time
                pack_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(general_path), f"-c={merged_main_path}", "-f=General", f"-r={general_path}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                pack_time = time.time() - pack_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to create {merged_main_path.name}: {result.stderr}")
                
                merged_size = merged_main_path.stat().st_size
                compression_ratio = (1 - merged_size / uncompressed_size) * 100 if uncompressed_size > 0 else 0
                self.logger.info(f"  Created in {pack_time:.1f}s: {merged_size / 1024 / 1024:.1f} MB ({compression_ratio:.1f}% compression)")
            
            # Pack Sounds BA2 (Uncompressed)
            if has_sounds:
                merged_sounds_path = data_path / f"{output_name} - Sounds.ba2"
                sound_file_count = sum(1 for _ in sounds_dir.rglob("*") if _.is_file())
                uncompressed_size = sum(f.stat().st_size for f in sounds_dir.rglob("*") if f.is_file())
                self.logger.info(f"Creating {merged_sounds_path.name} ({sound_file_count} files, {uncompressed_size / (1024**2):.2f} MB uncompressed)...")
                
                import time
                pack_start = time.time()
                result = subprocess.run(
                    [self.archive2_path, str(sounds_dir), 
                     f"-c={merged_sounds_path}", 
                     "-f=General",
                     "-compression=None",
                     f"-r={sounds_dir}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                pack_time = time.time() - pack_start
                
                if result.returncode != 0:
                    raise Exception(f"Failed to create {merged_sounds_path.name}: {result.stderr}")
                
                merged_size = merged_sounds_path.stat().st_size
                self.logger.info(f"Created {merged_sounds_path.name} (uncompressed) in {pack_time:.1f}s")
                self.logger.info(f"  Final: {merged_size / 1024 / 1024:.1f} MB, {sound_file_count} files")
            
            # Pack texture BA2s (with 4GB split)
            if texture_ba2s:
                texture_file_count = sum(1 for item in textures_path.rglob("*") if item.is_file())
                texture_files = [(item, item.stat().st_size) for item in textures_path.rglob("*") if item.is_file()]
                texture_files.sort(key=lambda x: x[1], reverse=True)
                
                # Split at 7GB uncompressed (targets ~3.5GB compressed)
                MAX_UNCOMPRESSED_SIZE = int(7.0 * 1024 * 1024 * 1024)
                self.logger.info(f"Using {MAX_UNCOMPRESSED_SIZE / (1024**3):.1f}GB uncompressed threshold (targets ~3.5GB compressed)")
                
                archive_groups = []
                current_group = []
                current_size = 0
                
                for file_path, file_size in texture_files:
                    if current_size + file_size > MAX_UNCOMPRESSED_SIZE and current_group:
                        archive_groups.append(current_group)
                        current_group = []
                        current_size = 0
                    current_group.append(file_path)
                    current_size += file_size
                
                if current_group:
                    archive_groups.append(current_group)
                
                total_uncompressed = sum(size for _, size in texture_files)
                self.logger.info(f"Total uncompressed texture data: {total_uncompressed / (1024**3):.2f}GB")
                self.logger.info(f"Splitting {texture_file_count} texture files into {len(archive_groups)} archives")
                
                import time
                for idx, file_group in enumerate(archive_groups, 1):
                    if len(archive_groups) == 1:
                        archive_name = f"{output_name} - Textures.ba2"
                    else:
                        archive_name = f"{output_name} - Textures{idx}.ba2"
                    
                    merged_textures_path = data_path / archive_name
                    group_uncompressed = sum(f.stat().st_size for f in file_group)
                    self.logger.info(f"Creating {archive_name} with {len(file_group)} files ({group_uncompressed / (1024**3):.2f}GB uncompressed)...")
                    
                    split_temp = temp_path / f"textures_split{idx}"
                    split_temp.mkdir(exist_ok=True)
                    
                    for file_path in file_group:
                        rel_path = file_path.relative_to(textures_path)
                        dest_path = split_temp / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                    
                    pack_start = time.time()
                    result = subprocess.run(
                        [self.archive2_path, str(split_temp), f"-c={merged_textures_path}", "-f=DDS", f"-r={split_temp}"],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    pack_time = time.time() - pack_start
                    
                    if result.returncode != 0:
                        raise Exception(f"Failed to create {archive_name}: {result.stderr}")
                    
                    merged_size = merged_textures_path.stat().st_size
                    compression_ratio = (1 - merged_size / group_uncompressed) * 100 if group_uncompressed > 0 else 0
                    merged_texture_paths.append(merged_textures_path)
                    self.logger.info(f"  Created {archive_name} in {pack_time:.1f}s: {merged_size / 1024 / 1024:.1f} MB ({compression_ratio:.1f}% compression)")
            
            # Create dummy ESL(s)
            created_esls = []
            dummy_esl = data_path / f"{output_name}.esl"
            self._create_dummy_esl(dummy_esl)
            created_esls.append(dummy_esl.name)
            
            # Create dummy ESL for sounds if they exist
            if has_sounds:
                sounds_esl = data_path / f"{output_name}_Sounds.esl"
                self._create_dummy_esl(sounds_esl)
                created_esls.append(sounds_esl.name)
            
            # Delete original BA2 files
            for ba2_file in all_ba2s:
                ba2_file.unlink()
            
            # Clean up temp directory
            shutil.rmtree(temp_path)
            
            # Summary statistics
            self.logger.info("="*60)
            self.logger.info(f"CUSTOM MERGE SUMMARY: {output_name}")
            self.logger.info(f"  Source: {len(mod_names)} mods, {len(all_ba2s)} BA2 files")
            merged_count = (1 if merged_main_path else 0) + len(merged_texture_paths) + (1 if has_sounds else 0)
            self.logger.info(f"  Merged: {merged_count} BA2 file(s) (Main, Textures, Sounds)")
            self.logger.info(f"  Reduction: {len(all_ba2s)} → {merged_count} ({(1 - merged_count/len(all_ba2s))*100:.1f}% fewer files)")
            
            total_original = original_main_size + original_texture_size
            total_merged = (merged_main_path.stat().st_size if merged_main_path else 0)
            total_merged += sum(p.stat().st_size for p in merged_texture_paths)
            total_merged += (merged_sounds_path.stat().st_size if merged_sounds_path else 0)
            self.logger.info(f"  Total space: {total_original / (1024**2):.1f} MB → {total_merged / (1024**2):.1f} MB")
            self.logger.info(f"  Space saved: {(total_original - total_merged) / (1024**2):.1f} MB ({((total_original - total_merged)/total_original*100):.1f}%)")
            self.logger.info(f"  Backup: {backup_path}")
            self.logger.info("="*60)
            self.logger.info(f"Custom merge completed: {output_name}")
            
            return {
                "success": True,
                "merged_main": str(merged_main_path) if merged_main_path else None,
                "merged_textures": [str(p) for p in merged_texture_paths] if merged_texture_paths else [],
                "texture_archive_count": len(merged_texture_paths) if merged_texture_paths else 0,
                "original_count": len(all_ba2s),
                "backup_path": str(backup_path),
                "dummy_esl": str(dummy_esl)
            }
            
        except Exception as e:
            self.logger.error(f"Error merging custom BA2s: {e}")
            if temp_path.exists():
                shutil.rmtree(temp_path)
            return {"success": False, "error": str(e)}
    
    def restore_cc_ba2s(self, backup_path: str, fo4_path: str, mod_name: str = "CCMerged") -> Dict[str, Any]:
        """
        Restore individual CC BA2 files from backup and remove merged archives.
        
        Args:
            backup_path: Path to backup folder containing original CC BA2s
            fo4_path: Path to Fallout 4 installation
            mod_name: Name of the merged mod folder to remove (default: "CCMerged")
            
        Returns:
            Dict with:
                - success: bool
                - restored_count: number of BA2s restored
                - removed_merged: list of removed merged files
                - error: error message (if failed)
        """
        backup = Path(backup_path)
        data_path = Path(fo4_path) / "Data"
        
        if not backup.exists():
            return {"success": False, "error": f"Backup folder not found: {backup_path}"}
        
        if not data_path.exists():
            return {"success": False, "error": "Fallout 4 Data folder not found"}
        
        try:
            self.logger.info(f"Restoring CC BA2s from backup: {backup_path}")
            
            # 1. Find all BA2 files in backup
            backup_ba2s = list(backup.glob("cc*.ba2"))
            if not backup_ba2s:
                return {"success": False, "error": "No CC BA2 files found in backup"}
            
            self.logger.info(f"Found {len(backup_ba2s)} CC BA2 files in backup")
            
            # 2. Remove merged mod folder from MO2 mods directory
            mods_path = Path(self.mo2_dir)
            mod_folder = mods_path / mod_name
            removed_files = []
            esl_files = []
            
            if mod_folder.exists():
                # Find all ESL files to unregister before deleting
                esl_files = [f.name for f in mod_folder.glob("*.esl")]
                
                # List what's being removed
                for item in mod_folder.iterdir():
                    removed_files.append(item.name)
                    self.logger.info(f"Removing merged file: {item.name}")
                
                shutil.rmtree(mod_folder)
                self.logger.info(f"Removed merged mod folder: {mod_folder}")
            
            # 3. Unregister mod from MO2 lists
            # If we found ESLs, unregister each one
            if esl_files:
                for esl in esl_files:
                    self._unregister_mo2_mod(mod_name, esl)
            else:
                # Fallback: try to unregister default name if folder was already gone
                self._unregister_mo2_mod(mod_name, f"{mod_name}.esl")
            
            # 4. Restore original CC BA2 files
            restored_count = 0
            for backup_ba2 in backup_ba2s:
                target_ba2 = data_path / backup_ba2.name
                shutil.copy2(backup_ba2, target_ba2)
                restored_count += 1
            
            self.logger.info(f"Restored {restored_count} CC BA2 files")
            
            # 5. Delete backup folder
            shutil.rmtree(backup)
            self.logger.info(f"Deleted backup folder: {backup_path}")
            
            self.logger.info("CC BA2 restoration completed successfully!")
            
            return {
                "success": True,
                "restored_count": restored_count,
                "removed_merged": removed_files
            }
            
        except Exception as e:
            self.logger.error(f"Error restoring CC BA2s: {e}")
            return {"success": False, "error": str(e)}
    
    def get_cc_merge_status(self, fo4_path: str, mod_name: str = "CCMerged") -> Dict[str, Any]:
        """
        Check if CC BA2s are currently merged.
        
        Args:
            fo4_path: Path to Fallout 4 installation
            mod_name: Name of the merged mod folder (default: "CCMerged")
            
        Returns:
            Dict with:
                - is_merged: bool (True if merged archives exist)
                - merged_files: list of merged BA2/ESL files
                - individual_cc_count: number of individual cc*.ba2 files
                - available_backups: list of available backup folders
        """
        data_path = Path(fo4_path) / "Data"
        backup_root = Path(self.backup_dir) / "CC_Merge_Backup"
        
        if not data_path.exists():
            return {"is_merged": False, "error": "Fallout 4 Data folder not found"}
        
        # Check for merged files in MO2 mod folder (new location)
        mods_path = Path(self.mo2_dir)
        mod_folder = mods_path / mod_name
        merged_files = []
        
        if mod_folder.exists():
            # Check for BA2 and ESL files in the mod folder
            for pattern in ["*.ba2", "*.esl"]:
                merged_files.extend([f.name for f in mod_folder.glob(pattern)])
        
        # OLD CODE (commented out - kept for reference in case we need fallback to Fallout4.ini method):
        # Check for merged files in Data folder (old location)
        # merged_files = []
        # for pattern in ["*Merged*.ba2", "*Merged*.esl", "CCMerged*.ba2", "CCMerged*.esl"]:
        #     merged_files.extend([f.name for f in data_path.glob(pattern)])
        
        is_merged = len(merged_files) > 0
        
        # Count individual CC BA2s in Data folder
        cc_ba2_count = len(list(data_path.glob("cc*.ba2")))
        
        # Find available backups
        available_backups = []
        if backup_root.exists():
            for backup_folder in backup_root.iterdir():
                if backup_folder.is_dir():
                    cc_count = len(list(backup_folder.glob("cc*.ba2")))
                    available_backups.append({
                        "path": str(backup_folder),
                        "name": backup_folder.name,
                        "cc_count": cc_count
                    })
        
        return {
            "is_merged": is_merged,
            "merged_files": merged_files,
            "individual_cc_count": cc_ba2_count,
            "available_backups": available_backups
        }
    
    def _create_dummy_esl(self, esl_path: Path) -> None:
        """
        Create a minimal dummy ESL file to load merged BA2 archives.
        
        This creates a proper ESL with TES4 header and required subrecords.
        The structure matches Bethesda's minimal plugin format.
        """
        # Proper TES4 record structure for Fallout 4
        esl_data = bytearray()
        
        # TES4 Record Header (24 bytes before subrecords)
        esl_data.extend(b'TES4')              # Record type (4 bytes)
        esl_data.extend(b'\x19\x00\x00\x00')  # Data size: 25 bytes (HEDR 18 + CNAM 7) (4 bytes)
        esl_data.extend(b'\x00\x00\x00\x00')  # Flags (4 bytes) - could set ESL flag 0x200 here
        esl_data.extend(b'\x00\x00\x00\x00')  # Form ID (4 bytes) 
        esl_data.extend(b'\x00\x00\x00\x00')  # Timestamp (4 bytes)
        esl_data.extend(b'\x00\x00\x00\x00')  # Version control (4 bytes)
        
        # HEDR subrecord (Header data) - 18 bytes total (4 type + 2 size + 12 data)
        esl_data.extend(b'HEDR')              # Subrecord type (4 bytes)
        esl_data.extend(b'\x0c\x00')          # Data size: 12 bytes (2 bytes)
        esl_data.extend(b'\x3f\x99\x99\x9a')  # Version 1.2 as float (4 bytes)
        esl_data.extend(b'\x00\x00\x00\x00')  # Number of records (4 bytes)
        esl_data.extend(b'\x00\x00\x00\x00')  # Next object ID (4 bytes)
        
        # CNAM subrecord (Author) - 7 bytes total (4 type + 2 size + 1 data)
        esl_data.extend(b'CNAM')              # Subrecord type (4 bytes)
        esl_data.extend(b'\x01\x00')          # Data size: 1 byte (2 bytes)
        esl_data.extend(b'\x00')              # Null-terminated empty string (1 byte)
        
        with open(esl_path, 'wb') as f:
            f.write(esl_data)
        
        self.logger.info(f"Created dummy ESL: {esl_path.name} ({len(esl_data)} bytes)")
