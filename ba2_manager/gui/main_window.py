"""Main application window"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QMessageBox, QListWidget, QListWidgetItem,
    QProgressBar, QGroupBox, QFormLayout, QFileDialog, QDialog,
    QDialogButtonBox, QLineEdit, QCheckBox, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from ba2_manager.core.ba2_handler import BA2Handler
from ba2_manager.config import Config
import os
import winreg
import webbrowser
import sys
from typing import Optional


class MainWindow(QMainWindow):
    """Main application window with menu-based layout"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        
        # Detect MO2 installation first to establish a portable root
        mo2_root = self.detect_mo2_installation()
        
        # Initialize paths with defaults or detection
        mo2_mods_dir = self.config.get("mo2_mods_dir", "")
        if not mo2_mods_dir or not os.path.exists(mo2_mods_dir):
            if mo2_root:
                # Check for custom mod directory in ModOrganizer.ini
                custom_mods_dir = self.get_custom_mods_directory(mo2_root)
                if custom_mods_dir and custom_mods_dir.exists():
                    mo2_mods_dir = str(custom_mods_dir)
                else:
                    mo2_mods_dir = str(mo2_root / "mods")
                self.config.set("mo2_mods_dir", mo2_mods_dir)
            else:
                mo2_mods_dir = "mods"

        # Enforce portable backup directory structure
        # If we found MO2, backups go to MO2/BA2_Manager_Backups
        # Otherwise they go to ./BA2_Manager_Backups
        backup_dir = self.config.get("backup_dir", "")
        # Always update backup_dir if we found MO2, to ensure portability
        if mo2_root:
            backup_dir = str(mo2_root / "BA2_Manager_Backups")
            self.config.set("backup_dir", backup_dir)
        elif not backup_dir:
            backup_dir = "BA2_Manager_Backups"
            self.config.set("backup_dir", backup_dir)

        archive2_path = self.config.get("archive2_path", "")
        fo4_path = self.config.get("fo4_path", "")
        
        # Auto-detect FO4 path from MO2 if missing
        if not fo4_path and mo2_root:
            detected_fo4 = self.detect_fo4_from_mo2(mo2_root)
            if detected_fo4:
                self.config.set("fo4_path", detected_fo4)
                fo4_path = detected_fo4

        # Auto-detect Archive2 if missing
        if not archive2_path:
            # Try registry first
            detected = self.detect_archive2_from_registry()
            if detected:
                self.config.set("archive2_path", detected)
                archive2_path = detected
            # If not in registry, try FO4 path if we have it
            elif fo4_path:
                archive2_candidate = Path(fo4_path) / "Tools" / "Archive2" / "Archive2.exe"
                if archive2_candidate.exists():
                    self.config.set("archive2_path", str(archive2_candidate))
                    archive2_path = str(archive2_candidate)
                
        log_file = self.config.get("log_file", "BA2_Extract.log")
        
        self.ba2_handler = BA2Handler(
            archive2_path=archive2_path if archive2_path else None,
            mo2_dir=mo2_mods_dir,
            backup_dir=backup_dir,
            log_file=log_file
        )
        self.current_view = None
        
        # Blink timer for danger state
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_bar)
        self.blink_state = False
        
        self.init_ui()
    
    def get_custom_mods_directory(self, mo2_root: Path) -> Optional[Path]:
        """
        Check ModOrganizer.ini for a custom 'mod_directory' setting.
        Returns the absolute path if found, otherwise None.
        """
        ini_path = mo2_root / "ModOrganizer.ini"
        if not ini_path.exists():
            return None
            
        try:
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_settings = False
                for line in f:
                    line = line.strip()
                    if line == "[Settings]":
                        in_settings = True
                        continue
                    elif line.startswith("[") and line.endswith("]"):
                        in_settings = False
                        continue
                        
                    if in_settings and line.startswith("mod_directory="):
                        value = line.split("=", 1)[1].strip()
                        if not value:
                            return None
                        
                        # Handle @ByteArray if present
                        if value.startswith("@ByteArray(") and value.endswith(")"):
                            value = value[11:-1]
                            # Handle escaped backslashes common in Qt settings
                            value = value.replace("\\\\", "\\")
                        
                        path_val = Path(value)
                        if path_val.is_absolute():
                            return path_val
                        else:
                            return mo2_root / path_val
        except Exception:
            pass
        return None
    
    def detect_mo2_installation(self) -> Path:
        """
        Search for ModOrganizer.ini in current, parent, and sibling directories.
        Useful if the app is placed inside or near the MO2 folder.
        """
        # Check current dir and up to 3 levels up
        current = Path.cwd()
        # Also check the executable's directory (important for PyInstaller)
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        
        search_paths = [current, exe_dir] + list(current.parents)[:3] + list(exe_dir.parents)[:3]
        
        # Check direct paths first
        for path in search_paths:
            ini_path = path / "ModOrganizer.ini"
            if ini_path.exists():
                return path
        
        # Check sibling directories for mo2_fo4 or MO2 folders
        for path in [current, exe_dir]:
            if path.parent.exists():
                for sibling in path.parent.iterdir():
                    if sibling.is_dir() and sibling.name.lower() in ['mo2_fo4', 'mo2', 'mods']:
                        ini_path = sibling / "ModOrganizer.ini"
                        if ini_path.exists():
                            return sibling
        
        return None

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("BA2 Manager")
        # Set default size to match expected layout (approx 1000x700)
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 650)
        
        # Set Window Icon
        # Check for icon in current dir or sys._MEIPASS (if frozen)
        icon_name = "app.ico"
        icon_path = Path(icon_name)
        
        if getattr(sys, 'frozen', False):
            # If frozen, look in the temp folder where PyInstaller extracts data
            base_path = Path(sys._MEIPASS)
            icon_path = base_path / icon_name
            
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Outer layout with content and bar
        outer_layout = QHBoxLayout()
        
        # BA2 Status Bar (left side)
        self.ba2_bar = self.create_ba2_status_bar()
        outer_layout.addWidget(self.ba2_bar)
        
        # Main content layout (right side)
        content_layout = QVBoxLayout()
        
        # Header with title and disclaimer
        header_layout = self.create_header()
        content_layout.addLayout(header_layout)
        
        # Main menu buttons
        menu_layout = self.create_main_menu()
        content_layout.addLayout(menu_layout)
        
        # Content area (will be replaced by different views)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_area.setLayout(self.content_layout)
        content_layout.addWidget(self.content_area)
        
        # Exit button at bottom
        exit_layout = QHBoxLayout()
        exit_layout.addStretch()
        
        # Version label
        version_label = QLabel("v1.1.0")
        version_label.setStyleSheet("color: gray; margin-right: 10px;")
        exit_layout.addWidget(version_label)
        
        exit_btn = QPushButton("Exit")
        exit_btn.setMaximumWidth(150)
        exit_btn.clicked.connect(self.close)
        exit_layout.addWidget(exit_btn)
        content_layout.addLayout(exit_layout)
        
        # Add content layout to outer layout
        outer_layout.addLayout(content_layout)
        
        central_widget.setLayout(outer_layout)
        
        # Show BA2 Information by default
        self.show_ba2_info()
    
    def create_header(self):
        """Create header with title and disclaimer"""
        layout = QVBoxLayout()
        
        title = QLabel("BA2 Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        disclaimer = QLabel("WARNING: This tool modifies your Fallout 4 installation. Always backup before making changes.")
        disclaimer.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        layout.addWidget(disclaimer)
        
        layout.addSpacing(10)
        return layout
    
    def create_main_menu(self):
        """Create main menu buttons"""
        layout = QHBoxLayout()
        layout.addSpacing(20)
        
        # BA2 Information button
        info_btn = QPushButton("BA2 Information")
        info_btn.setMinimumWidth(150)
        info_btn.setMinimumHeight(50)
        info_btn.clicked.connect(self.show_ba2_info)
        layout.addWidget(info_btn)
        
        # Manage Mod BA2s button
        manage_btn = QPushButton("Extract/Restore Mod BA2s")
        manage_btn.setMinimumWidth(150)
        manage_btn.setMinimumHeight(50)
        manage_btn.clicked.connect(self.show_manage_mods)
        layout.addWidget(manage_btn)
        
        # Manage Creation Club button
        cc_btn = QPushButton("Manage Creation Club")
        cc_btn.setMinimumWidth(150)
        cc_btn.setMinimumHeight(50)
        cc_btn.clicked.connect(self.show_manage_cc)
        layout.addWidget(cc_btn)
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setMinimumWidth(150)
        settings_btn.setMinimumHeight(50)
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        layout.addSpacing(20)
        return layout
    
    def create_ba2_status_bar(self):
        """Create vertical BA2 status bar for left side"""
        bar_widget = QWidget()
        bar_layout = QVBoxLayout()
        bar_layout.setContentsMargins(10, 10, 10, 10)
        bar_layout.setSpacing(5)
        
        # Title
        title = QLabel("BA2 Counts")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(title)
        
        # Main BA2 section
        main_label = QLabel("Main")
        main_font = QFont()
        main_font.setPointSize(8)
        main_label.setFont(main_font)
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(main_label)
        
        self.ba2_main_value = QLabel("0")
        value_font = QFont()
        value_font.setPointSize(12)
        value_font.setBold(True)
        self.ba2_main_value.setFont(value_font)
        self.ba2_main_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(self.ba2_main_value)
        
        # Main bars container
        main_bar_container = QHBoxLayout()
        main_bar_container.addStretch()
        self.ba2_main_progress = QProgressBar()
        self.ba2_main_progress.setOrientation(Qt.Orientation.Vertical)
        self.ba2_main_progress.setMinimum(0)
        self.ba2_main_progress.setMaximum(255)
        self.ba2_main_progress.setValue(0)
        self.ba2_main_progress.setTextVisible(False)
        self.ba2_main_progress.setFixedWidth(25)
        self.ba2_main_progress.setMinimumHeight(200)
        self.update_ba2_bar_style_main(0, 255)
        main_bar_container.addWidget(self.ba2_main_progress)
        main_bar_container.addStretch()
        bar_layout.addLayout(main_bar_container)
        
        # Texture BA2 section
        texture_label = QLabel("Textures")
        texture_label.setFont(main_font)
        texture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(texture_label)
        
        self.ba2_texture_value = QLabel("0")
        self.ba2_texture_value.setFont(value_font)
        self.ba2_texture_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(self.ba2_texture_value)
        
        # Texture bars container
        texture_bar_container = QHBoxLayout()
        texture_bar_container.addStretch()
        self.ba2_texture_progress = QProgressBar()
        self.ba2_texture_progress.setOrientation(Qt.Orientation.Vertical)
        self.ba2_texture_progress.setMinimum(0)
        self.ba2_texture_progress.setMaximum(254)
        self.ba2_texture_progress.setValue(0)
        self.ba2_texture_progress.setTextVisible(False)
        self.ba2_texture_progress.setFixedWidth(25)
        self.ba2_texture_progress.setMinimumHeight(200)
        self.update_ba2_bar_style_texture(0, 254)
        texture_bar_container.addWidget(self.ba2_texture_progress)
        texture_bar_container.addStretch()
        bar_layout.addLayout(texture_bar_container)
        
        bar_widget.setLayout(bar_layout)
        bar_widget.setMaximumWidth(90)
        return bar_widget
    
    def update_ba2_bar_style_main(self, value: int, limit: int):
        """Update the main BA2 bar - green until max, then red blinking"""
        if value > limit:
            if not self.blink_timer.isActive():
                self.blink_timer.start(500)
            self.ba2_main_progress.setValue(limit)
            self.ba2_main_value.setText(str(value))
            self.ba2_main_value.setStyleSheet("color: #FF0000; font-weight: bold;")
            return
        
        if self.blink_timer.isActive():
            self.blink_timer.stop()
            self.blink_state = False
        
        self.ba2_main_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        self.ba2_main_value.setText(str(value))
        self.ba2_main_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.ba2_main_progress.setValue(value)
    
    def update_ba2_bar_style_texture(self, value: int, limit: int):
        """Update the texture BA2 bar - green until max, then red blinking"""
        if value > limit:
            if not self.blink_timer.isActive():
                self.blink_timer.start(500)
            self.ba2_texture_progress.setValue(limit)
            self.ba2_texture_value.setText(str(value))
            self.ba2_texture_value.setStyleSheet("color: #FF0000; font-weight: bold;")
            return
        
        if self.blink_timer.isActive():
            self.blink_timer.stop()
            self.blink_state = False
        
        self.ba2_texture_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        self.ba2_texture_value.setText(str(value))
        self.ba2_texture_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.ba2_texture_progress.setValue(value)

    def update_ba2_bar_style(self, value: int):
        """Update the BA2 bar color based on value with smooth gradient"""
        
        # Handle blinking for danger state (> 500)
        if value > 500:
            if not self.blink_timer.isActive():
                self.blink_timer.start(500) # Blink every 500ms
            
            # Ensure bar is full
            self.ba2_progress.setValue(501)
            
            # Update status text immediately
            self.ba2_value_label.setText(str(value))
            self.ba2_status_label.setText("DANGER")
            self.ba2_value_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            return

        # Stop blinking if safe
        if self.blink_timer.isActive():
            self.blink_timer.stop()
            self.blink_state = False
        
        # Calculate color based on value with smooth gradient
        # Green (0, 255, 0) to Red (255, 0, 0)
        
        # Cap value at 500 for color calculation
        calc_value = min(max(value, 0), 500)
        
        if calc_value <= 250:
            # Green to Yellow
            r = int(255 * (calc_value / 250))
            g = 255
            b = 0
        else:
            # Yellow to Red
            r = 255
            g = int(255 * ((500 - calc_value) / 250))
            b = 0
            
        color = f"rgb({r}, {g}, {b})"
        
        self.ba2_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        
        # Determine status text and color
        if value > 350:
            status = "WARNING"
            label_style = "color: #FFB74D; font-weight: bold;"
        else:
            status = "SAFE"
            label_style = "color: #4CAF50; font-weight: bold;"
            
        self.ba2_value_label.setText(str(value))
        self.ba2_status_label.setText(status)
        self.ba2_value_label.setStyleSheet(label_style)
        self.ba2_progress.setValue(value)

    def blink_bar(self):
        """Toggle bar color for blinking effect"""
        self.blink_state = not self.blink_state
        
        # Toggle between Bright Red and Dark Red
        color = "#FF0000" if self.blink_state else "#550000"
        
        self.ba2_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
    
    def clear_content(self):
        """Clear the content area"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_ba2_info(self):
        """Show BA2 information view"""
        self.clear_content()
        
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        
        # Title
        title = QLabel("BA2 Count Information")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        info_layout.addWidget(title)
        
        # Info group with detailed breakdown
        info_group = QGroupBox("BA2 File Count Summary")
        group_layout = QVBoxLayout()
        
        # Header row for columns
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Category"), 2)
        header_layout.addWidget(QLabel("Main"), 1)
        header_layout.addWidget(QLabel("Texture"), 1)
        group_layout.addLayout(header_layout)
        
        # Separator
        separator = QLabel("─" * 50)
        separator.setStyleSheet("color: gray;")
        group_layout.addWidget(separator)
        
        # Base Game Categories with Main/Texture columns
        self.info_main_main = QLabel("--")
        self.info_main_texture = QLabel("--")
        main_layout = QHBoxLayout()
        main_layout.addWidget(QLabel("Main Game Files:"), 2)
        main_layout.addWidget(self.info_main_main, 1)
        main_layout.addWidget(self.info_main_texture, 1)
        group_layout.addLayout(main_layout)
        
        self.info_dlc_main = QLabel("--")
        self.info_dlc_texture = QLabel("--")
        dlc_layout = QHBoxLayout()
        dlc_layout.addWidget(QLabel("DLC Files:"), 2)
        dlc_layout.addWidget(self.info_dlc_main, 1)
        dlc_layout.addWidget(self.info_dlc_texture, 1)
        group_layout.addLayout(dlc_layout)
        
        self.info_cc_main = QLabel("--")
        self.info_cc_texture = QLabel("--")
        cc_layout = QHBoxLayout()
        cc_layout.addWidget(QLabel("Creation Club (CC):"), 2)
        cc_layout.addWidget(self.info_cc_main, 1)
        cc_layout.addWidget(self.info_cc_texture, 1)
        group_layout.addLayout(cc_layout)
        
        self.info_creation_store_main = QLabel("--")
        self.info_creation_store_texture = QLabel("--")
        cs_layout = QHBoxLayout()
        cs_layout.addWidget(QLabel("Creation Store Mods:"), 2)
        cs_layout.addWidget(self.info_creation_store_main, 1)
        cs_layout.addWidget(self.info_creation_store_texture, 1)
        group_layout.addLayout(cs_layout)
        
        self.info_mods_main = QLabel("--")
        self.info_mods_texture = QLabel("--")
        mods_layout = QHBoxLayout()
        mods_layout.addWidget(QLabel("Mod BA2s (MO2):"), 2)
        mods_layout.addWidget(self.info_mods_main, 1)
        mods_layout.addWidget(self.info_mods_texture, 1)
        group_layout.addLayout(mods_layout)
        
        self.info_replacements = QLabel("--")
        replacements_layout = QHBoxLayout()
        replacements_layout.addWidget(QLabel("Vanilla Replacements:"), 2)
        replacements_layout.addWidget(self.info_replacements, 1)
        replacements_layout.addWidget(QLabel(""), 1)
        group_layout.addLayout(replacements_layout)
        
        # Separator
        separator2 = QLabel("─" * 50)
        separator2.setStyleSheet("color: gray;")
        group_layout.addWidget(separator2)
        
        # Total row
        self.info_total = QLabel("--")
        total_layout = QHBoxLayout()
        total_label = QLabel("TOTAL BA2 FILES:")
        total_label.setStyleSheet("font-weight: bold;")
        total_layout.addWidget(total_label, 2)
        total_layout.addWidget(self.info_total, 2)
        group_layout.addLayout(total_layout)
        
        # Warning messages at bottom
        warning_layout = QVBoxLayout()
        warning1 = QLabel("⚠ Exceeding 255 Main BA2 files will cause the game to crash on startup.")
        warning1.setStyleSheet("color: #FF0000; font-weight: bold; margin-top: 10px;")
        warning2 = QLabel("⚠ Exceeding 254 Texture BA2 files will cause graphical corruption in your game.")
        warning2.setStyleSheet("color: #FF0000; font-weight: bold;")
        warning_layout.addWidget(warning1)
        warning_layout.addWidget(warning2)
        group_layout.addLayout(warning_layout)
        
        info_group.setLayout(group_layout)
        info_layout.addWidget(info_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Count")
        refresh_btn.clicked.connect(self.refresh_ba2_count)
        info_layout.addWidget(refresh_btn)
        
        # Status and recommendations
        self.info_status = QTextEdit()
        self.info_status.setReadOnly(True)
        self.info_status.setMaximumHeight(60)
        info_layout.addWidget(self.info_status)
        
        info_layout.addStretch()
        info_widget.setLayout(info_layout)
        self.content_layout.addWidget(info_widget)
        
        # Load initial count immediately
        self.refresh_ba2_count()
        
        # Auto-refresh on display
        self.refresh_ba2_count()
    
    def show_manage_mods(self):
        """
        Display the Manage Mod BA2s view with checkbox-based extraction/restoration interface.
        
        WORKFLOW:
        1. User sees list of all BA2 mods with checkboxes (unchecked by default)
        2. By default, all mods are unchecked (normal BA2 archive format state)
        3. User checks mods they want to extract (decompress to loose files)
        4. User clicks 'Apply Changes' to execute the operation
        5. Checked mods turn GREEN (extracted/loose files state)
        6. Unchecked mods turn BLACK (normal BA2 archive state)
        
        STATE TRACKING:
        - self.mod_extracted_status: dict mapping list index -> bool (True=extracted, False=not extracted/normal)
        - This tracks the CURRENT state after operations, not the initial state
        - Used to detect changes: if checkbox state != tracked state, operation is needed
        """
        self.clear_content()
        
        manage_widget = QWidget()
        manage_layout = QVBoxLayout()
        
        # === HEADER ===
        title = QLabel("Manage Mod BA2s")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        manage_layout.addWidget(title)
        
        # === INSTRUCTIONS ===
        instructions = QLabel("Check boxes to select mods. Checked mods will be extracted, unchecked mods will be restored.")
        manage_layout.addWidget(instructions)
        
        # Show Backup Directory
        backup_dir = self.config.get("backup_dir", "Unknown")
        backup_label = QLabel(f"Backup Directory: {backup_dir}")
        backup_label.setStyleSheet("color: gray; font-style: italic;")
        manage_layout.addWidget(backup_label)
        
        # === MOD LIST ===
        # The list displays all BA2 mods from the MO2 mods directory with checkboxes
        # Each item is a QTableWidgetItem with ItemIsUserCheckable flag enabled
        list_label = QLabel("Available BA2 Mods:")
        manage_layout.addWidget(list_label)
        
        self.mod_list = QTableWidget()
        self.mod_list.setColumnCount(2)
        self.mod_list.setHorizontalHeaderLabels(["Mod Name", "Nexus Link"])
        self.mod_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mod_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.mod_list.verticalHeader().setVisible(False)
        self.mod_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.mod_extracted_status = {}  # {index: bool} - tracks current state of each mod
        manage_layout.addWidget(self.mod_list)
        
        # === ACTION BUTTON ===
        # Single button applies all checkbox changes at once
        # Logic: compares current checkbox state with tracked state, performs necessary operations
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        restore_all_btn = QPushButton("Restore All Extracted")
        restore_all_btn.setMaximumWidth(200)
        restore_all_btn.clicked.connect(self.restore_all_mods)
        button_layout.addWidget(restore_all_btn)
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setMaximumWidth(200)
        apply_btn.clicked.connect(self.apply_mod_changes)
        button_layout.addWidget(apply_btn)
        
        manage_layout.addLayout(button_layout)
        
        # Status
        status_label = QLabel("Status:")
        manage_layout.addWidget(status_label)
        
        self.mod_status = QTextEdit()
        self.mod_status.setReadOnly(True)
        self.mod_status.setMaximumHeight(60)
        self.mod_status.setText("Loading mod list...")
        manage_layout.addWidget(self.mod_status)
        
        manage_layout.addStretch()
        manage_widget.setLayout(manage_layout)
        self.content_layout.addWidget(manage_widget)
        
        # Load mod list (don't refresh count here - widgets don't exist)
        self.load_mod_list()
    
    def show_manage_cc(self):
        """Show manage Creation Club view"""
        self.clear_content()
        
        cc_widget = QWidget()
        cc_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Manage Creation Club Content")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        cc_layout.addWidget(title)
        
        instructions = QLabel("Enable or disable Creation Club packages:")
        cc_layout.addWidget(instructions)
        
        # CC list
        list_label = QLabel("Available CC Content:")
        cc_layout.addWidget(list_label)
        
        self.cc_list = QListWidget()
        cc_layout.addWidget(self.cc_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.apply_cc_changes)
        apply_btn.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        button_layout.addWidget(apply_btn)
        
        enable_all_btn = QPushButton("Enable All")
        enable_all_btn.clicked.connect(self.enable_all_cc)
        button_layout.addWidget(enable_all_btn)
        
        disable_all_btn = QPushButton("Disable All")
        disable_all_btn.clicked.connect(self.disable_all_cc)
        button_layout.addWidget(disable_all_btn)
        
        cc_layout.addLayout(button_layout)
        
        # Status
        status_label = QLabel("Status:")
        cc_layout.addWidget(status_label)
        
        self.cc_status = QTextEdit()
        self.cc_status.setReadOnly(True)
        self.cc_status.setMaximumHeight(60)
        cc_layout.addWidget(self.cc_status)
        
        cc_layout.addStretch()
        cc_widget.setLayout(cc_layout)
        self.content_layout.addWidget(cc_widget)
        
        # Load CC list
        self.load_cc_list()
    
    def show_settings(self):
        """Show settings view"""
        self.clear_content()
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        settings_layout.addWidget(title)
        
        instructions = QLabel("Click 'Find' to locate executable files. Paths will be automatically configured.")
        settings_layout.addWidget(instructions)
        
        # Settings group
        settings_group = QGroupBox("Configuration")
        form_layout = QFormLayout()
        
        # Mod Organizer 2
        mo2_layout = QHBoxLayout()
        self.settings_mo2_display = QLineEdit()
        self.settings_mo2_display.setReadOnly(True)
        self.settings_mo2_display.setText(self.config.get("mo2_mods_dir", ""))
        mo2_layout.addWidget(self.settings_mo2_display)
        find_mo2 = QPushButton("Find ModOrganizer.exe")
        find_mo2.setMaximumWidth(200)
        find_mo2.clicked.connect(self.find_mo2_exe)
        mo2_layout.addWidget(find_mo2)
        form_layout.addRow("Mod Organizer:", mo2_layout)
        
        # Archive2.exe
        archive2_layout = QHBoxLayout()
        self.settings_archive2_display = QLineEdit()
        self.settings_archive2_display.setReadOnly(True)
        
        current_archive2 = self.config.get("archive2_path", "")
        # Auto-detect if empty
        if not current_archive2:
            detected = self.detect_archive2_from_registry()
            if detected:
                current_archive2 = detected
        
        self.settings_archive2_display.setText(current_archive2)
        archive2_layout.addWidget(self.settings_archive2_display)
        
        find_archive2 = QPushButton("Find Archive2.exe")
        find_archive2.setMaximumWidth(200)
        find_archive2.clicked.connect(self.find_archive2_exe)
        archive2_layout.addWidget(find_archive2)
        form_layout.addRow("Archive2.exe:", archive2_layout)
        
        # Add link if still empty
        if not current_archive2:
             link_label = QLabel('<a href="https://store.steampowered.com/app/1946160/Fallout_4_Creation_Kit/">Download Creation Kit (Steam)</a>')
             link_label.setOpenExternalLinks(True)
             form_layout.addRow("", link_label)
        
        # Fallout 4
        fo4_layout = QHBoxLayout()
        self.settings_fo4_display = QLineEdit()
        self.settings_fo4_display.setReadOnly(True)
        self.settings_fo4_display.setText(self.config.get("fo4_path", ""))
        fo4_layout.addWidget(self.settings_fo4_display)
        find_fo4 = QPushButton("Find Fallout4.exe")
        find_fo4.setMaximumWidth(200)
        find_fo4.clicked.connect(self.find_fallout4_exe)
        fo4_layout.addWidget(find_fo4)
        form_layout.addRow("Fallout 4:", fo4_layout)
        
        # DEBUG: Add a temporary label to confirm UI update path
        debug_label = QLabel("DEBUG CHECKBOX TEST")
        form_layout.addRow(debug_label)
        # Debug Logging Checkbox
        self.debug_logging_checkbox = QCheckBox("Enable Debug Logging (for troubleshooting)")
        self.debug_logging_checkbox.setChecked(self.config.get("debug_logging", False))
        form_layout.addRow("Debug Logging:", self.debug_logging_checkbox)
        settings_group.setLayout(form_layout)
        settings_layout.addWidget(settings_group)
        
        # Status
        self.settings_status = QTextEdit()
        self.settings_status.setReadOnly(True)
        self.settings_status.setMaximumHeight(60)
        settings_layout.addWidget(QLabel("Configuration Status:"))
        settings_layout.addWidget(self.settings_status)
        self.update_settings_status()
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_btn)
        
        # View logs button
        logs_btn = QPushButton("View Operation Logs")
        logs_btn.clicked.connect(self.show_logs)
        settings_layout.addWidget(logs_btn)
        
        # License button
        license_btn = QPushButton("View License")
        license_btn.clicked.connect(self.show_license)
        settings_layout.addWidget(license_btn)
        
        settings_layout.addStretch()
        settings_widget.setLayout(settings_layout)
        self.content_layout.addWidget(settings_widget)
    
    def safe_set_text(self, widget_name, text):
        """Safely set text on a widget that might have been deleted"""
        try:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if widget:
                    widget.setText(text)
        except RuntimeError:
            # Widget has been deleted (C++ object gone)
            pass

    def safe_set_style(self, widget_name, style):
        """Safely set stylesheet on a widget that might have been deleted"""
        try:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if widget:
                    widget.setStyleSheet(style)
        except RuntimeError:
            pass

    def refresh_ba2_count(self):
        """Refresh BA2 count with separate Main and Texture counts"""
        try:
            fo4_path = self.config.get("fo4_path", "")
            if not fo4_path:
                self.safe_set_text('info_status', "ERROR: Fallout 4 path not configured in Settings")
                self.update_ba2_bar_style_main(0, 255)
                self.update_ba2_bar_style_texture(0, 254)
                return
            
            counts = self.ba2_handler.count_ba2_files(fo4_path)
            main_total = counts["main_total"]
            texture_total = counts["texture_total"]
            
            # Update the two progress bars
            self.update_ba2_bar_style_main(main_total, 255)
            self.update_ba2_bar_style_texture(texture_total, 254)
            
            # Update all the category counts with Main/Texture columns
            # Main Game
            self.safe_set_text('info_main_main', str(counts["main"]))
            self.safe_set_text('info_main_texture', "0")
            
            # DLC
            self.safe_set_text('info_dlc_main', str(counts["dlc"]))
            self.safe_set_text('info_dlc_texture', str(counts.get("dlc_textures", 0)))
            
            # Creation Club
            self.safe_set_text('info_cc_main', str(counts["creation_club"]))
            self.safe_set_text('info_cc_texture', str(counts.get("creation_club_textures", 0)))
            
            # Creation Store Mods
            self.safe_set_text('info_creation_store_main', str(counts["creation_store"]))
            self.safe_set_text('info_creation_store_texture', str(0))
            
            # Mod BA2s
            self.safe_set_text('info_mods_main', str(counts["mod_main"]))
            self.safe_set_text('info_mods_texture', str(counts.get("mod_textures", 0)))
            
            # Replacements (just show the count, no texture split needed)
            self.safe_set_text('info_replacements', f"{counts['replacements']} (not counted)")
            
            # Total
            main_str = f"{main_total}/255"
            texture_str = f"{texture_total}/254"
            self.safe_set_text('info_total', f"Main: {main_str} | Textures: {texture_str}")
            
            # Color code based on limits exceeded
            if main_total > 255 or texture_total > 254:
                self.safe_set_style('info_total', "color: #FF6B6B; font-weight: bold;")
                status = "STATUS: OVER LIMIT - One or more BA2 categories exceeded!"
            else:
                self.safe_set_style('info_total', "color: #4CAF50; font-weight: bold;")
                status = "STATUS: SAFE - All BA2 counts within limits"
            
            self.safe_set_text('info_status', status)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.safe_set_text('info_status', f"Error counting BA2s: {str(e)}")
            self.update_ba2_bar_style_main(0, 255)
            self.update_ba2_bar_style_texture(0, 254)
    
    def load_mod_list(self):
        """
        Load and populate the mod list.
        
        IMPLEMENTATION NOTES:
        - QTableWidgetItem with CheckState sets initial checkbox state
        - Qt.ItemFlag.ItemIsUserCheckable enables checkbox interaction
        - UserRole data stores the actual mod name for reference
        - Index maps directly to mod_extracted_status dict
        - Checkbox checked = extract to loose files; unchecked = BA2 archive format (default)
        """
        try:
            mods = self.ba2_handler.list_ba2_mods()
            self.mod_list.setRowCount(0)  # Clear table
            self.mod_extracted_status = {}
            
            for i, mod in enumerate(mods):
                self.mod_list.insertRow(i)
                
                # === FORMAT DISPLAY TEXT ===
                size_mb = mod.size / 1024 / 1024
                item_text = f"{mod.mod_name} ({size_mb:.1f} MB)"
                
                # === CREATE MOD NAME ITEM WITH CHECKBOX (Column 0) ===
                item = QTableWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, mod.mod_name)  # Store mod name for reference
                
                # Set state based on whether mod is already extracted
                if mod.is_extracted:
                    item.setCheckState(Qt.CheckState.Checked)
                    item.setForeground(QColor("#4CAF50"))  # Green for extracted
                    item.setToolTip("Status: Extracted (No BA2s found, Backup exists)")
                    self.mod_extracted_status[i] = True
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.mod_extracted_status[i] = False
                    
                    if mod.has_backup:
                        # Backup exists but BA2s are present -> Not fully extracted or restored
                        item.setToolTip("Status: Not Extracted (BA2s present). Backup exists.")
                    else:
                        item.setToolTip("Status: Not Extracted (BA2s present)")
                    
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Enable checkbox
                self.mod_list.setItem(i, 0, item)
                
                # === CREATE NEXUS LINK ITEM (Column 1) ===
                if mod.nexus_url:
                    link_label = QLabel(f'<a href="{mod.nexus_url}">Nexus Page</a>')
                    link_label.setOpenExternalLinks(True)
                    link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.mod_list.setCellWidget(i, 1, link_label)
                else:
                    self.mod_list.setItem(i, 1, QTableWidgetItem(""))

            # === UPDATE STATUS ===
            if not mods:
                self.mod_status.setText("No BA2 mods found in MO2 directory")
            else:
                self.mod_status.setText(f"Found {len(mods)} BA2 mod(s)")
        except Exception as e:
            self.mod_status.setText(f"Error loading mods: {str(e)}")
    
    def load_cc_list(self):
        """
        Load and populate the CC packages list.
        
        Gets all available CC packages from ba2_handler and populates the list
        with checkable items showing which are currently active.
        """
        try:
            fo4_path = self.config.get("fo4_path", "")
            if not fo4_path:
                self.cc_status.setText("ERROR: Fallout 4 path not configured in Settings")
                return
            
            # Ensure master backup exists (created on first load)
            self.ba2_handler.create_cc_master_backup(fo4_path)
            
            # Get CC packages with their active status
            cc_packages = self.ba2_handler.get_cc_packages(fo4_path)
            
            self.cc_list.clear()
            for plugin_id, display_name, is_active in cc_packages:
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, plugin_id)  # Store plugin ID
                
                # Set checked state based on active status
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                if is_active:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                
                self.cc_list.addItem(item)
            
            # Update status
            active_count = sum(1 for _, _, is_active in cc_packages if is_active)
            self.cc_status.setText(f"Found {len(cc_packages)} CC package(s)\n{active_count} currently enabled")
        except Exception as e:
            self.cc_status.setText(f"Error loading CC packages: {str(e)}")
    
    def apply_mod_changes(self):
        """
        Execute extraction/restoration based on checkbox states.
        
        NEW WORKFLOW:
        - User checks boxes -> items turn GREY (pending extraction)
        - User clicks "Apply Changes" -> extraction happens
        - After completion -> items turn GREEN (extraction complete)
        - User unchecks box -> item turns BLACK (restored/normal)
        """
        changes_made = False
        extracted_count = 0
        restored_count = 0
        failed_count = 0
        
        # Disable UI during operation
        self.setEnabled(False)
        self.mod_status.setText("Processing changes... Please wait.")
        QApplication.processEvents()
        
        try:
            for i in range(self.mod_list.rowCount()):
                item = self.mod_list.item(i, 0)
                mod_name = item.data(Qt.ItemDataRole.UserRole)
                
                if not mod_name:
                    continue
                
                # === CHECK CURRENT CHECKBOX STATE ===
                is_checked = item.checkState() == Qt.CheckState.Checked
                
                # === GET TRACKED STATE ===
                was_extracted = self.mod_extracted_status.get(i, False)
                
                # === DETECT STATE CHANGE ===
                if is_checked != was_extracted:
                    changes_made = True
                    
                    if is_checked:
                        # User checked box -> EXTRACT this mod
                        self.pending_extraction(i)
                        QApplication.processEvents()
                        
                        if self.ba2_handler.extract_mod(mod_name):
                            self.mark_mod_extracted(i)
                            extracted_count += 1
                        else:
                            # Failed - revert visual state
                            item.setCheckState(Qt.CheckState.Unchecked)
                            self.unmark_mod_extracted(i)
                            failed_count += 1
                            
                    else:
                        # User unchecked box -> RESTORE this mod
                        if self.ba2_handler.restore_mod(mod_name):
                            self.unmark_mod_extracted(i)
                            restored_count += 1
                        else:
                            # Failed - revert visual state
                            item.setCheckState(Qt.CheckState.Checked)
                            self.mark_mod_extracted(i)
                            failed_count += 1
            
            # === REPORT RESULTS ===
            if not changes_made:
                self.mod_status.setText("No changes to apply.")
            else:
                message = "Operation complete!"
                if extracted_count > 0:
                    message += f"\nExtracted {extracted_count} mod(s)."
                if restored_count > 0:
                    message += f"\nRestored {restored_count} mod(s)."
                if failed_count > 0:
                    message += f"\nFailed operations: {failed_count}. Check logs."
                self.mod_status.setText(message)
                
                # Refresh the BA2 count bar
                self.refresh_ba2_count()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.mod_status.setText(f"Error applying changes: {e}")
        finally:
            self.setEnabled(True)
    
    def pending_extraction(self, index: int):
        """
        Mark a mod as PENDING EXTRACTION and update visual state.
        
        This is called when the user checks a checkbox to show that extraction
        is queued/in-progress.
        
        UPDATES:
        1. Item text color: Changes to GREY (#808080)
           Grey indicates the BA2 extraction is PENDING/IN PROGRESS
        2. Does NOT update mod_extracted_status yet (still in process)
        
        NOTE: This is a temporary state. After extraction completes,
        mark_mod_extracted() is called to turn it green.
        """
        item = self.mod_list.item(index, 0)
        if item is None:
            return
        
        # === UPDATE VISUAL STATE ===
        # Grey color signals: this mod extraction is PENDING
        item.setForeground(QColor("#808080"))
    
    def mark_mod_extracted(self, index: int):
        """
        Mark a mod as EXTRACTED and update visual state.
        
        This is called when an extraction operation completes successfully.
        
        UPDATES:
        1. Item text color: Changes to GREEN (#4CAF50)
           Green indicates the BA2 is EXTRACTED/COMPRESSED state
        2. Tracking dict: Sets mod_extracted_status[index] = True
           This records the current state for future comparisons
        
        NOTE: This is the final state after extraction completes.
        """
        item = self.mod_list.item(index, 0)
        if item is None:
            return
        
        # === UPDATE VISUAL STATE ===
        # Green color signals: this mod is in EXTRACTED state
        item.setForeground(QColor("#4CAF50"))
        
        # === UPDATE TRACKING STATE ===
        # Record that this mod is now considered extracted
        self.mod_extracted_status[index] = True
    
    def unmark_mod_extracted(self, index: int):
        """
        Mark a mod as RESTORED and update visual state.
        
        This is called when the user unchecks a checkbox or when a restoration
        operation completes successfully.
        
        UPDATES:
        1. Item text color: Resets to default (Theme color)
           Default color indicates the BA2 is RESTORED/NORMAL state
        2. Tracking dict: Sets mod_extracted_status[index] = False
           This records the current state for future comparisons
        
        NOTE: This is a UI/state update only. The actual BA2 file decompression
        would be handled by the backend Archive2.exe integration (future feature).
        """
        item = self.mod_list.item(index, 0)
        if item is None:
            return
        
        # === UPDATE VISUAL STATE ===
        # Reset color to default theme color (clears the green/grey override)
        item.setData(Qt.ItemDataRole.ForegroundRole, None)
        
        # === UPDATE TRACKING STATE ===
        # Record that this mod is now considered restored
        self.mod_extracted_status[index] = False
    
    def enable_all_cc(self):
        """Check all CC items and apply changes with confirmation"""
        reply = QMessageBox.question(
            self, 
            "Confirm Enable All", 
            "Are you sure you want to enable ALL Creation Club content?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for i in range(self.cc_list.count()):
                item = self.cc_list.item(i)
                item.setCheckState(Qt.CheckState.Checked)
            self.apply_cc_changes()

    def disable_all_cc(self):
        """Uncheck all CC items and apply changes with confirmation"""
        reply = QMessageBox.question(
            self, 
            "Confirm Disable All", 
            "Are you sure you want to disable ALL Creation Club content?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for i in range(self.cc_list.count()):
                item = self.cc_list.item(i)
                item.setCheckState(Qt.CheckState.Unchecked)
            self.apply_cc_changes()

    def apply_cc_changes(self):
        """Apply changes to Fallout4.ccc based on checkbox states"""
        try:
            fo4_path = self.config.get("fo4_path", "")
            if not fo4_path:
                QMessageBox.warning(self, "Error", "Fallout 4 path not configured.")
                return
                
            enabled_plugins = []
            
            # Gather all checked items
            for i in range(self.cc_list.count()):
                item = self.cc_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    # UserRole stores the full filename (e.g. "ccbgsfo4001.esl")
                    plugin_filename = item.data(Qt.ItemDataRole.UserRole)
                    if plugin_filename:
                        enabled_plugins.append(plugin_filename)
            
            # Call handler to write the file
            if self.ba2_handler.write_ccc_file(fo4_path, enabled_plugins):
                self.cc_status.setText(f"Successfully updated Fallout4.ccc with {len(enabled_plugins)} active plugins.")
                self.refresh_ba2_count()
            else:
                self.cc_status.setText("Error updating Fallout4.ccc. Check logs for details.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Crash prevented in apply_cc_changes: {e}")
    
    def find_mo2_exe(self):
        """Find ModOrganizer.exe and configure paths"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Find ModOrganizer.exe",
            "",
            "Executable Files (*.exe)"
        )
        if file_path and file_path.lower().endswith("modorganizer.exe"):
            # Extract MO2 root (parent of modorganizer.exe location)
            mo2_root = str(Path(file_path).parent)
            mods_path = str(Path(mo2_root) / "mods")
            backup_path = str(Path(mo2_root) / "BA2_Manager_Backups")
            
            self.settings_mo2_display.setText(mods_path)
            self.config.set("mo2_mods_dir", mods_path)
            self.config.set("backup_dir", backup_path)
            
            # Attempt to auto-detect Fallout 4 path from MO2 config
            fo4_path = self.detect_fo4_from_mo2(mo2_root)
            if fo4_path:
                self.settings_fo4_display.setText(fo4_path)
                self.config.set("fo4_path", fo4_path)
                
                # If we found FO4, try to find Archive2 inside it
                archive2_path = Path(fo4_path) / "Tools" / "Archive2" / "Archive2.exe"
                if archive2_path.exists():
                    self.settings_archive2_display.setText(str(archive2_path))
                    self.config.set("archive2_path", str(archive2_path))
            
            # Reinitialize BA2Handler with new MO2 path
            self.ba2_handler = BA2Handler(
                archive2_path=self.config.get("archive2_path") or None,
                mo2_dir=mods_path,
                log_file=self.config.get("log_file", "BA2_Extract.log")
            )
            
            self.update_settings_status()
            
            msg = f"ModOrganizer found!\nMods path: {mods_path}\nBackups: {backup_path}"
            if fo4_path:
                msg += f"\nFallout 4 detected: {fo4_path}"
            
            QMessageBox.information(self, "Success", msg)
        elif file_path:
            QMessageBox.warning(self, "Error", "Please select ModOrganizer.exe")
    
    def find_archive2_exe(self):
        """Find Archive2.exe and configure path"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Find Archive2.exe",
            "",
            "Executable Files (*.exe)"
        )
        if file_path and file_path.lower().endswith("archive2.exe"):
            self.settings_archive2_display.setText(file_path)
            self.config.set("archive2_path", file_path)
            
            # Reinitialize BA2Handler with new Archive2 path
            self.ba2_handler = BA2Handler(
                archive2_path=file_path,
                mo2_dir=self.config.get("mo2_mods_dir", "mods"),
                log_file=self.config.get("log_file", "BA2_Extract.log")
            )
            
            self.update_settings_status()
            QMessageBox.information(self, "Success", f"Archive2.exe found!\nPath: {file_path}")
        elif file_path:
            QMessageBox.warning(self, "Error", "Please select Archive2.exe")
    
    def find_fallout4_exe(self):
        """Find Fallout4.exe and configure paths"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Find Fallout4.exe",
            "",
            "Executable Files (*.exe)"
        )
        if file_path and file_path.lower().endswith("fallout4.exe"):
            # Extract Fallout 4 root (parent directory of Fallout4.exe)
            fo4_root = str(Path(file_path).parent)
            self.settings_fo4_display.setText(fo4_root)
            self.config.set("fo4_path", fo4_root)
            self.update_settings_status()
            QMessageBox.information(self, "Success", f"Fallout 4 found!\nPath: {fo4_root}")
        elif file_path:
            QMessageBox.warning(self, "Error", "Please select Fallout4.exe")
    
    def detect_archive2_from_registry(self):
        """Attempt to detect Archive2.exe path from Registry"""
        try:
            key_path = r"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4"
            # Open the key
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                # Try to read 'Installed Path'
                install_path, _ = winreg.QueryValueEx(key, "Installed Path")
                
                if install_path:
                    # Construct potential Archive2 path
                    archive2_path = Path(install_path) / "Tools" / "Archive2" / "Archive2.exe"
                    
                    if archive2_path.exists():
                        return str(archive2_path)
        except Exception as e:
            # Registry key not found or other error
            print(f"Registry detection failed: {e}")
            return None
        return None

    def detect_fo4_from_mo2(self, mo2_root: str) -> str:
        """
        Attempt to detect Fallout 4 path from ModOrganizer.ini
        
        Logic:
        1. Look for ModOrganizer.ini in mo2_root
        2. Parse for 'gamePath' key
        3. Handle @ByteArray(...) format if present
        """
        try:
            ini_path = Path(mo2_root) / "ModOrganizer.ini"
            if not ini_path.exists():
                return None
                
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().startswith('gamePath='):
                        # Extract value after gamePath=
                        value = line.strip().split('=', 1)[1]
                        
                        # Handle @ByteArray(path) format
                        if value.startswith('@ByteArray(') and value.endswith(')'):
                            # Extract content between parenthesis
                            path_str = value[11:-1]
                            # Replace double backslashes
                            path_str = path_str.replace('\\\\', '\\')
                            return path_str
                        else:
                            # Standard format
                            return value.strip()
        except Exception as e:
            print(f"Error reading ModOrganizer.ini: {e}")
            return None
        return None

    def update_settings_status(self):
        """Update configuration status display"""
        # Safety check for deleted widget
        if not hasattr(self, 'settings_status') or self.settings_status is None:
            return

        status_lines = []
        
        mo2_path = self.config.get("mo2_mods_dir", "")
        archive2_path = self.config.get("archive2_path", "")
        fo4_path = self.config.get("fo4_path", "")
        
        status_lines.append("Configuration Status:")
        status_lines.append("-" * 40)
        
        if mo2_path:
            status_lines.append("✓ MO2 Mods: Configured")
        else:
            status_lines.append("✗ MO2 Mods: Not configured")
        
        if archive2_path:
            status_lines.append("✓ Archive2.exe: Configured")
        else:
            status_lines.append("✗ Archive2.exe: Not configured")
        
        if fo4_path:
            status_lines.append("✓ Fallout 4: Configured")
        else:
            status_lines.append("✗ Fallout 4: Not configured")
        
        try:
            self.settings_status.setText("\n".join(status_lines))
        except RuntimeError:
            # Widget has been deleted
            pass
    
    def save_settings(self):
        """Save settings"""
        try:
            # Check for deleted widgets before accessing
            try:
                self.config.update({
                    "archive2_path": self.settings_archive2_display.text(),
                    "mo2_mods_dir": self.settings_mo2_display.text(),
                    "fo4_path": self.settings_fo4_display.text(),
                    "debug_logging": self.debug_logging_checkbox.isChecked(),
                })
            except RuntimeError:
                # Widgets have been deleted
                return
            
            # Reinitialize BA2Handler with new paths
            mo2_mods_dir = self.config.get("mo2_mods_dir", "mods")
            archive2_path = self.config.get("archive2_path", "")
            log_file = self.config.get("log_file", "BA2_Extract.log")
            
            self.ba2_handler = BA2Handler(
                archive2_path=archive2_path if archive2_path else None,
                mo2_dir=mo2_mods_dir,
                log_file=log_file
            )
            
            # Refresh BA2 count with new settings
            self.refresh_ba2_count()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.update_settings_status()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving settings: {str(e)}")
    
    def show_logs(self):
        """Show operation logs"""
        self.clear_content()
        logs_widget = QWidget()
        logs_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Operation Logs")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        logs_layout.addWidget(title)
        
        # Get log content
        try:
            logs = self.ba2_handler.get_log_entries(100)
            logs_text = QTextEdit()
            logs_text.setReadOnly(True)
            logs_text.setText(logs if logs else "No log entries found.")
            logs_layout.addWidget(logs_text)
        except Exception as e:
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setText(f"Error reading logs: {str(e)}")
            logs_layout.addWidget(error_text)
        
        logs_layout.addStretch()
        logs_widget.setLayout(logs_layout)
        self.content_layout.addWidget(logs_widget)
    
    def restore_all_mods(self):
        """
        Restore ALL currently extracted mods to their original state.
        """
        # Confirmation dialog
        confirm = QMessageBox.question(
            self, 
            "Confirm Restore All",
            "Are you sure you want to restore ALL extracted mods?\nThis will delete loose files and restore original BA2 archives.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return

        restored_count = 0
        failed_count = 0
        
        self.setEnabled(False)
        self.mod_status.setText("Restoring all mods... Please wait.")
        QApplication.processEvents()
        
        try:
            # Iterate through all items
            for i in range(self.mod_list.rowCount()):
                item = self.mod_list.item(i, 0)
                mod_name = item.data(Qt.ItemDataRole.UserRole)
                
                # Check if currently extracted
                if self.mod_extracted_status.get(i, False):
                    if self.ba2_handler.restore_mod(mod_name):
                        self.unmark_mod_extracted(i)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        restored_count += 1
                    else:
                        failed_count += 1
            
            self.mod_status.setText(f"Restore All Complete: Restored {restored_count} mods. Failed: {failed_count}")
            
            # Refresh the BA2 count bar
            self.refresh_ba2_count()
            
        except Exception as e:
            self.mod_status.setText(f"Error during Restore All: {str(e)}")
        finally:
            self.setEnabled(True)
    
    def show_license(self):
        """Show MIT License in a popup"""
        license_text = """MIT License

Copyright (c) 2025 jturnley

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        
        QMessageBox.information(self, "MIT License", license_text)
