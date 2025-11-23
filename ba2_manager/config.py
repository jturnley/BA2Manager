"""Configuration management for BA2 Manager

This module handles persistent storage and retrieval of application settings.
All user configuration is stored in ba2_manager_config.json.

KEY SETTINGS:
- archive2_path: Path to Archive2.exe (needed for extraction/restoration)
- mo2_mods_dir: Path to MO2 mods directory (where mod BA2s live)
- fo4_path: Path to Fallout 4 installation root
- backup_dir: Path to backup directory for extracted BA2s
- log_file: Path to operation log file

FILE LOCATION:
- ba2_manager_config.json (created in working directory on first run)
- JSON format for human readability

AUTO-CREATION:
- If config file doesn't exist, it's created with DEFAULT_CONFIG
- User then configures paths via Settings UI
- Once configured, settings persist across application restarts
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """
    Persistent configuration manager using JSON file.
    
    RESPONSIBILITIES:
    1. Load configuration from disk on startup
    2. Save changes immediately when user modifies settings
    3. Provide type-safe get/set interface to application
    4. Create default config if file doesn't exist
    
    INITIALIZATION:
    - Config() loads from ba2_manager_config.json
    - If file missing, creates it with DEFAULT_CONFIG
    - Application then must call config.set() to populate paths
    
    PERSISTENCE:
    - Every set() or update() immediately writes to disk
    - No in-memory-only changes (always persisted)
    - Survives application crashes
    """
    
    CONFIG_FILE = "ba2_manager_config.json"
    
    # DEFAULT CONFIGURATION
    # User must fill in these paths via Settings UI
    DEFAULT_CONFIG = {
        "archive2_path": "",           # User finds Archive2.exe
        "mo2_mods_dir": "",            # Auto-derived from ModOrganizer.exe
        "fo4_path": "",                # User finds Fallout4.exe
        "log_file": "ba2-manager.log",  # Can use default
        "backup_dir": "",              # Auto-derived from MO2 root
        "debug_logging": False
    }
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize configuration manager.
        
        PROCESS:
        1. Check if ba2_manager_config.json exists
        2. If yes: Load it
        3. If no: Create with DEFAULT_CONFIG
        
        PARAMETERS:
            config_file (str): Filename for config (usually ba2_manager_config.json)
        
        EXAMPLE:
            config = Config()  # Load or create default
            archive2 = config.get("archive2_path")  # Get value
            config.set("mo2_mods_dir", "C:\\MO2\\mods")  # Set and save
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file or create with defaults.
        
        LOGIC:
        - If ba2_manager_config.json exists → parse JSON and return
        - If parsing fails → log error and return DEFAULT_CONFIG
        - If file doesn't exist → call save_config() to create it
        
        RETURNS:
            Dict with all configuration keys and values
        
        ERROR HANDLING:
        - File read errors: Fall back to DEFAULT_CONFIG
        - JSON parse errors: Fall back to DEFAULT_CONFIG
        - Returns loaded config on success
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG.copy())
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """
        Save configuration to JSON file.
        
        PARAMETERS:
            config (Dict, optional): If provided, save this dict
                                    If None, save self.config (current state)
        
        CALLED BY:
        - __init__() when creating new config
        - set() after updating single value
        - update() after updating multiple values
        
        ERROR HANDLING:
        - File write errors print warning but don't crash
        - Always uses indent=2 for human readability
        
        FILE FORMAT:
        Writes pretty-printed JSON like:
        {
          "archive2_path": "C:\\Archive2.exe",
          "mo2_mods_dir": "C:\\MO2\\mods",
          ...
        }
        """
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value safely.
        
        PARAMETERS:
            key (str): Configuration key to retrieve
                      Examples: "archive2_path", "mo2_mods_dir", "fo4_path"
            
            default (Any, optional): Value to return if key not found
                                    Defaults to None
        
        RETURNS:
            Configuration value if found, otherwise default
        
        USAGE:
            path = config.get("archive2_path", "")  # Default to empty string
            if config.get("mo2_mods_dir"):  # Check if configured
                print("MO2 path is set")
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set single configuration value and save to disk.
        
        PARAMETERS:
            key (str): Configuration key to set
            value (Any): Value to set
        
        BEHAVIOR:
        - Updates self.config[key] = value
        - Immediately calls save_config() to persist
        - Used for single-value updates
        
        USAGE:
            config.set("archive2_path", "C:\\Archive2.exe")
            config.set("mo2_mods_dir", "C:\\MO2\\mods")
        
        DIFFERS FROM update():
        - set(): Single key-value pair, called frequently
        - update(): Multiple key-value pairs, called once
        """
        self.config[key] = value
        self.save_config()
    
    def update(self, values: Dict[str, Any]):
        """
        Update multiple configuration values at once and save.
        
        PARAMETERS:
            values (Dict): Dictionary of key-value pairs to update
        
        BEHAVIOR:
        - Updates multiple keys at once
        - Calls save_config() only once at end
        - More efficient than multiple set() calls
        
        USAGE:
            config.update({
                "archive2_path": "C:\\Archive2.exe",
                "mo2_mods_dir": "C:\\MO2\\mods",
                "fo4_path": "C:\\Fallout 4"
            })
        
        DIFFERS FROM set():
        - set(): Single key, called frequently
        - update(): Multiple keys, called less often
        """
        self.config.update(values)
        self.save_config()
