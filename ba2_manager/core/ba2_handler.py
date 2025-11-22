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
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BA2Info:
    """
    Data structure representing a single BA2 file.
    
    Attributes:
        path: Full file path to the BA2 file
        size: File size in bytes
        mod_name: Display name of the mod (directory name or extracted from filename)
        is_extracted: Boolean flag (for future: whether this BA2 is currently extracted)
        file_count: Number of files contained in this BA2 (for future use)
    
    Used by list_ba2_mods() to return mod BA2 information to the GUI.
    """
    path: str
    size: int
    mod_name: str
    is_extracted: bool = False
    file_count: int = 0


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
    - logger: FileHandler logging all operations to BA2_Extract.log
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
        "DLCRobot.ba2",
        "DLCRobot - Textures.ba2",
        "DLCworkshop01.ba2",
        "DLCworkshop01 - Textures.ba2",
        "DLCCoast.ba2",
        "DLCCoast - Textures.ba2",
        "DLCNukaWorld.ba2",
        "DLCNukaWorld - Textures.ba2",
    ]
    
    def __init__(self, archive2_path: Optional[str] = None, mo2_dir: Optional[str] = None, log_file: Optional[str] = None):
        r"""
        Initialize BA2 handler with paths and logging.
        
        PARAMETERS:
            archive2_path (str, optional): Full path to Archive2.exe
                - Used for future extraction/restoration operations
                - Not required for BA2 counting
                - Example: "C:\path\to\Archive2.exe"
            
            mo2_dir (str, optional): Path to MO2 mods directory
                - Required to scan for mod BA2 files
                - Expected structure: mods/**/*.ba2 (recursive)
                - Defaults to "mods" if not provided
            
            log_file (str, optional): Path to log file
                - All operations logged here for debugging
                - Defaults to "BA2_Extract.log" in working directory
                - Appends to existing file on restart
        
        LOGGING SETUP:
        - Creates FileHandler appending to log_file
        - Sets format: "timestamp - level - message"
        - Clears any existing handlers to avoid duplicates
        - Handles permission errors gracefully
        
        INITIALIZATION NOTES:
        - This is called when application starts and when settings change
        - If mo2_dir doesn't exist, logging will show "Mods directory does not exist"
        - Check BA2_Extract.log if counting returns unexpected values
        """
        self.archive2_path = archive2_path
        self.mo2_dir = mo2_dir or "mods"
        self.log_file = log_file or "BA2_Extract.log"
        self.failed_extractions = []
        
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
            handler1 = logging.FileHandler("BA2_Extract.log", mode='a')
            handler1.setLevel(logging.DEBUG)
            handler1.setFormatter(formatter)
            self.logger.addHandler(handler1)
        except Exception as e:
            print(f"Warning: Could not set up logging to BA2_Extract.log: {e}")
        # Always log to /dist/BA2_Extract.log
        try:
            handler2 = logging.FileHandler("dist/BA2_Extract.log", mode='a')
            handler2.setLevel(logging.DEBUG)
            handler2.setFormatter(formatter)
            self.logger.addHandler(handler2)
        except Exception as e:
            print(f"Warning: Could not set up logging to dist/BA2_Extract.log: {e}")
        # Always log to console
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        except Exception as e:
            print(f"Warning: Could not set up console logging: {e}")
        self.logger.info(f"BA2Handler initialized - mods_dir={self.mo2_dir}, log_file={self.log_file}, debug_logging={debug_logging}")
    
    def count_ba2_files(self, fo4_path: str) -> Dict:
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
        Each step logs to BA2_Extract.log for debugging:
        - Paths being scanned
        - Active CC plugins found
        - Each BA2 file categorized with explanation
        - Final counts
        
        TROUBLESHOOTING:
        If counts look wrong, check BA2_Extract.log for:
        - "Mods path exists: False" → mo2_dir not configured
        - "Fallout4.ccc not found" → fo4_path incorrect
        - "0 BA2 files in mods" → Check rglob is working
        """
        main_count = 0
        dlc_count = 0
        cc_count = 0
        creation_store_count = 0
        vanilla_ba2_names = set()
        
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
                    vanilla_ba2_names.add(ba2_name)
                    
                    # Categorize BA2 files exactly like PowerShell script
                    if ba2_name.startswith("cc"):
                        # For CC BA2s, only count if plugin is active in Fallout4.ccc
                        ba2_base = ba2_file.stem  # Remove extension
                        # Handle names like "ccbgsfo4119-cyberdog - main.ba2"
                        ba2_base = re.sub(r' - (main|textures)$', '', ba2_base, flags=re.IGNORECASE)
                        
                        if ba2_base in active_cc_plugins:
                            cc_count += 1
                    elif ba2_name.startswith("dlc"):
                        dlc_count += 1
                    elif ba2_name.startswith("fallout4 - "):
                        main_count += 1
                    else:
                        # Creation Store Mods (encrypted, non-extractable)
                        creation_store_count += 1
        
        # Count mod BA2s (excluding those that replace vanilla BA2s)
        mod_count = 0
        replacement_count = 0
        
        mods_path = Path(self.mo2_dir)
        self.logger.info(f"Scanning mods path: {mods_path}")
        self.logger.info(f"Mods path exists: {mods_path.exists()}")
        
        if mods_path.exists():
            mod_ba2s = list(mods_path.rglob("*.ba2"))
            self.logger.info(f"Found {len(mod_ba2s)} BA2 files in mods")
            
            for ba2_file in mod_ba2s:
                ba2_name = ba2_file.name.lower()
                self.logger.info(f"  Checking mod BA2: {ba2_file.relative_to(mods_path)}")
                
                if ba2_name in vanilla_ba2_names:
                    replacement_count += 1
                    self.logger.info(f"    -> Vanilla replacement")
                else:
                    mod_count += 1
                    self.logger.info(f"    -> New mod BA2")
        else:
            self.logger.warning(f"Mods directory does not exist: {mods_path}")
        
        base_game_count = main_count + dlc_count + cc_count + creation_store_count
        total = base_game_count + mod_count
        
        self.logger.info(f"Count summary: Main={main_count}, DLC={dlc_count}, CC={cc_count}, CreationStore={creation_store_count}, Mods={mod_count}, Total={total}")
        
        return {
            "main": main_count,
            "dlc": dlc_count,
            "creation_club": cc_count,
            "creation_store": creation_store_count,
            "base_game": base_game_count,
            "mods": mod_count,
            "replacements": replacement_count,
            "vanilla_ba2_names": vanilla_ba2_names,
            "total": total,
            "limit": 255
        }
    
    def _get_active_cc_plugins(self, fo4_path: str) -> set:
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
    
    def list_ba2_mods(self) -> List[BA2Info]:
        """List all BA2 mod files"""
        ba2_files = []
        mods_path = Path(self.mo2_dir)
        
        if mods_path.exists():
            try:
                for ba2_file in mods_path.rglob("*.ba2"):
                    try:
                        # Determine if it's in an extracted or BA2 folder
                        is_extracted = False
                        mod_name = ba2_file.parent.name
                        
                        # Safely get file size
                        try:
                            file_size = ba2_file.stat().st_size
                        except (OSError, IOError) as e:
                            self.logger.warning(f"Could not stat file {ba2_file}: {e}")
                            continue
                        
                        ba2_info = BA2Info(
                            path=str(ba2_file),
                            size=file_size,
                            mod_name=mod_name,
                            is_extracted=is_extracted
                        )
                        ba2_files.append(ba2_info)
                    except Exception as e:
                        self.logger.warning(f"Error processing BA2 file {ba2_file}: {e}")
                        continue
            except Exception as e:
                self.logger.error(f"Error listing BA2 mods in {self.mo2_dir}: {e}")
        else:
            self.logger.info(f"Mods directory does not exist: {self.mo2_dir}")
        
        return sorted(ba2_files, key=lambda x: x.mod_name)
    
    def extract_ba2_file(self, ba2_path: str, output_dir: str = None) -> bool:
        """Extract a BA2 file using Archive2.exe
        
        Args:
            ba2_path: Path to BA2 file to extract
            output_dir: Output directory for extracted files
            
        Returns:
            True if successful, False otherwise
        """
        if not self.archive2_path or not os.path.exists(self.archive2_path):
            self.logger.error("Archive2.exe not found")
            return False
        
        if not os.path.exists(ba2_path):
            self.logger.error(f"BA2 file not found: {ba2_path}")
            return False
        
        try:
            if output_dir is None:
                output_dir = os.path.dirname(ba2_path)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Run Archive2.exe to extract
            cmd = [self.archive2_path, "-extract", ba2_path, "-output", output_dir]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully extracted: {ba2_path}")
                return True
            else:
                self.logger.error(f"Failed to extract {ba2_path}: {result.stderr.decode()}")
                self.failed_extractions.append(ba2_path)
                return False
        except Exception as e:
            self.logger.error(f"Error extracting {ba2_path}: {str(e)}")
            self.failed_extractions.append(ba2_path)
            return False
    
    def repack_ba2_file(self, source_dir: str, output_ba2: str) -> bool:
        """Repack loose files into a BA2 archive
        
        Args:
            source_dir: Directory containing files to pack
            output_ba2: Output BA2 file path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.archive2_path or not os.path.exists(self.archive2_path):
            self.logger.error("Archive2.exe not found")
            return False
        
        try:
            cmd = [self.archive2_path, "-create", source_dir, "-output", output_ba2]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully created: {output_ba2}")
                return True
            else:
                self.logger.error(f"Failed to create {output_ba2}: {result.stderr.decode()}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating {output_ba2}: {str(e)}")
            return False
    
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
            
            # Write the file
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
