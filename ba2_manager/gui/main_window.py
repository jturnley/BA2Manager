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
import sys
import logging
import zipfile
from datetime import datetime
from typing import Optional


class CenteredCheckBox(QWidget):
    """Helper widget to center a checkbox in a table cell"""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.checkbox = QPushButton()
        self.checkbox.setCheckable(True)
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.clicked.connect(self.update_style)
        
        self.is_extracted_state = False
        
        layout.addWidget(self.checkbox)
        self.update_style()

    def isChecked(self) -> bool:
        return self.checkbox.isChecked()
        
    def setChecked(self, state: bool) -> None:
        self.checkbox.setChecked(state)
        self.update_style()
        
    def checkState(self) -> Qt.CheckState:
        return Qt.CheckState.Checked if self.checkbox.isChecked() else Qt.CheckState.Unchecked
        
    def setCheckState(self, state: Qt.CheckState) -> None:
        self.checkbox.setChecked(state == Qt.CheckState.Checked)
        self.update_style()
        
    def set_extracted(self, is_extracted: bool):
        """Set the visual state for extracted/restored"""
        self.is_extracted_state = is_extracted
        # If extracted, it must be checked initially
        if is_extracted:
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)
        self.update_style()

    def update_style(self):
        """Update the button style based on state"""
        is_checked = self.checkbox.isChecked()
        
        if self.is_extracted_state:
            if is_checked:
                # State: Extracted (Green)
                self.checkbox.setText("✓")
                self.checkbox.setStyleSheet("""
                    QPushButton {
                        background-color: #2D5016;
                        border: 1px solid #4CAF50;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                self.checkbox.setToolTip("Mod is Extracted")
            else:
                # State: Pending Restore (Red/Warning)
                self.checkbox.setText("✕")
                self.checkbox.setStyleSheet("""
                    QPushButton {
                        background-color: #501616;
                        border: 1px solid #FF5252;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                self.checkbox.setToolTip("Will be Restored (Click Apply)")
        else:
            if is_checked:
                # State: Pending Extract (Blue/Standard)
                self.checkbox.setText("✓")
                self.checkbox.setStyleSheet("""
                    QPushButton {
                        background-color: #1E88E5;
                        border: 1px solid #64B5F6;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                self.checkbox.setToolTip("Will be Extracted (Click Apply)")
            else:
                # State: Packed (Grey/Empty)
                self.checkbox.setText("")
                self.checkbox.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        border: 1px solid #666666;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        border: 1px solid #999999;
                    }
                """)
                self.checkbox.setToolTip("Mod is Packed")


class MainWindow(QMainWindow):
    """Main application window with menu-based layout"""
    
    def __init__(self):
        super().__init__()
        # Setup logging early
        self.logger = logging.getLogger("ba2_manager.gui")
        self.logger.debug("=== BA2 Manager Initialization Starting ===")
        self.logger.debug(f"Python version: {sys.version}")
        self.logger.debug(f"PyQt6 version: PyQt6")
        
        self.config = Config()
        
        # Detect MO2 installation only if ModOrganizer.ini sits beside the app
        self.logger.debug("Detecting MO2 installation (application directory only)...")
        mo2_root = self.detect_mo2_installation()
        if mo2_root:
            self.logger.debug(f"MO2 root found: {mo2_root}")
        else:
            self.logger.debug("ModOrganizer.ini not found near application; user must configure paths manually")
        
        # Initialize paths with defaults or detection
        mo2_mods_dir = self.config.get("mo2_mods_dir", "")
        if mo2_mods_dir and os.path.exists(mo2_mods_dir):
            self.logger.debug(f"Using configured MO2 mods directory: {mo2_mods_dir}")
        else:
            if mo2_mods_dir:
                self.logger.warning(f"Configured MO2 mods directory not found: {mo2_mods_dir}. Please update Settings")
            else:
                self.logger.debug("MO2 mods directory not configured yet; waiting for user selection")
            mo2_mods_dir = ""
            if mo2_root:
                self.logger.debug(f"ModOrganizer.ini detected at {mo2_root}, but will wait for user confirmation in Settings")

        # Enforce portable backup directory structure
        # Backups should always be relative to MO2, never the application directory
        backup_dir = self.config.get("backup_dir", "")
        # Always update backup_dir if we found MO2, to ensure portability
        if mo2_root:
            backup_dir = str(mo2_root / "BA2_Manager_Backups")
            self.config.set("backup_dir", backup_dir)
            self.logger.debug(f"Set backup_dir (MO2): {backup_dir}")
        elif not backup_dir:
            # No MO2 found and no backup_dir configured
            # BA2Handler will default to relative path based on mo2_mods_dir
            # Don't set a relative path in config - let the handler determine it
            backup_dir = None
            self.logger.debug("Backup dir will be determined by BA2Handler based on mo2_mods_dir")

        mo2_configured = bool(mo2_mods_dir and os.path.exists(mo2_mods_dir))
        mo2_detection_root = Path(mo2_mods_dir).parent if mo2_configured else mo2_root

        archive2_path = self.config.get("archive2_path", "")
        if archive2_path and not Path(archive2_path).exists():
            self.logger.warning(f"Configured Archive2.exe not found at {archive2_path}; re-detecting")
            archive2_path = ""
        fo4_path = self.config.get("fo4_path", "")
        
        # Auto-detect FO4 path from MO2 if missing
        if not fo4_path and mo2_root:
            self.logger.debug("Detecting Fallout 4 path from MO2...")
            detected_fo4 = self.detect_fo4_from_mo2(str(mo2_root))
            if detected_fo4:
                self.config.set("fo4_path", detected_fo4)
                fo4_path = detected_fo4
                self.logger.debug(f"Fallout 4 path detected: {detected_fo4}")
            else:
                self.logger.debug("Fallout 4 path not found in MO2")

        # Auto-detect Archive2 if missing
        if not archive2_path:
            if not mo2_configured or not mo2_detection_root:
                self.logger.debug("MO2 not configured; delaying Archive2 auto-detection until MO2 is selected")
            else:
                self.logger.debug("Detecting Archive2.exe...")
                detected = None

                # 1) Look inside the MO2 root (portable installs often bundle Archive2 here)
                if mo2_detection_root:
                    mo2_candidate = Path(mo2_detection_root) / "Archive2.exe"
                else:
                    mo2_candidate = None
                if mo2_candidate and mo2_candidate.exists():
                    detected = mo2_candidate
                    self.logger.debug(f"Archive2.exe found in MO2 root: {mo2_candidate}")
                else:
                    self.logger.debug(f"Archive2.exe not found in MO2 root: {mo2_candidate}")

                # 2) Look inside Fallout 4 Tools directory if not already found
                if not detected and fo4_path:
                    archive2_candidate = Path(fo4_path) / "Tools" / "Archive2" / "Archive2.exe"
                    if archive2_candidate.exists():
                        detected = archive2_candidate
                        self.logger.debug(f"Archive2.exe found in FO4 tools: {archive2_candidate}")
                    else:
                        self.logger.debug(f"Archive2.exe not found at: {archive2_candidate}")

                # 3) Fall back to registry detection last
                if not detected:
                    registry_candidate = self.detect_archive2_from_registry()
                    if registry_candidate:
                        detected = Path(registry_candidate)
                        self.logger.debug(f"Archive2.exe found via registry: {registry_candidate}")

                if detected:
                    archive2_path = str(detected)
                    self.config.set("archive2_path", archive2_path)
        else:
            self.logger.debug(f"Archive2.exe already configured: {archive2_path}")
                
        log_file = self.config.get("log_file", "ba2-manager.log")
        self.logger.debug(f"Log file: {log_file}")
        
        self.ba2_handler = BA2Handler(
            archive2_path=archive2_path if archive2_path else None,
            mo2_dir=mo2_mods_dir if mo2_mods_dir else None,
            backup_dir=backup_dir if backup_dir else None,
            log_file=log_file
        )
        self.logger.debug("=== BA2 Manager Initialization Complete ===")
        self.current_view = None
        
        self.init_ui()
        self.show_default_view()
    
    def get_custom_mods_directory(self, mo2_root: Path) -> Optional[Path]:
        """
        Check ModOrganizer.ini for a custom 'mod_directory' setting.
        Returns the absolute path if found, otherwise None.
        """
        ini_path = mo2_root / "ModOrganizer.ini"
        if not ini_path.exists():
            self.logger.debug(f"ModOrganizer.ini not found at: {ini_path}")
            return None
            
        try:
            self.logger.debug(f"Checking ModOrganizer.ini for custom mod_directory: {ini_path}")
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
                            self.logger.debug("mod_directory setting is empty")
                            return None
                        
                        # Handle @ByteArray if present
                        if value.startswith("@ByteArray(") and value.endswith(")"):
                            if len(value) > 12:  # Minimum length check for "@ByteArray()"
                                value = value[11:-1]
                                # Handle escaped backslashes common in Qt settings
                                value = value.replace("\\\\", "\\")
                            else:
                                self.logger.debug("Empty ByteArray value detected")
                                return None
                        
                        path_val = Path(value)
                        if path_val.is_absolute():
                            self.logger.debug(f"Custom mod_directory found: {path_val}")
                            return path_val
                        else:
                            resolved = mo2_root / path_val
                            self.logger.debug(f"Custom mod_directory found (relative): {resolved}")
                            return resolved
        except Exception as e:
            self.logger.debug(f"Error reading ModOrganizer.ini: {e}")
            pass
        return None
    
    def detect_mo2_installation(self) -> Optional[Path]:
        """Return MO2 root only if ModOrganizer.ini sits beside the application."""
        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
        ini_path = app_dir / "ModOrganizer.ini"
        self.logger.debug(f"Looking for ModOrganizer.ini in application directory: {ini_path}")
        if ini_path.exists():
            self.logger.debug("ModOrganizer.ini located next to application")
            return app_dir
        self.logger.debug("ModOrganizer.ini not found next to application; skipping auto-detection")
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
        version_label = QLabel("v2.0.0")
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

    def show_default_view(self):
        """Open Settings when critical paths missing, otherwise BA2 info."""
        required_values = [
            self.config.get("mo2_mods_dir", ""),
            self.config.get("archive2_path", ""),
            self.config.get("fo4_path", "")
        ]
        if all(required_values):
            self.logger.debug("All critical paths configured; showing BA2 Information view")
            self.show_ba2_info()
        else:
            self.logger.info("Critical paths missing; opening Settings view by default")
            self.show_settings()
    
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
        
        # Merge BA2s button
        merge_btn = QPushButton("Merge CC BA2s")
        merge_btn.setMinimumWidth(150)
        merge_btn.setMinimumHeight(50)
        merge_btn.clicked.connect(self.show_merge_ba2s)
        layout.addWidget(merge_btn)
        
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
        """Update the main BA2 bar - green until max, then red"""
        if value > limit:
            self.ba2_main_progress.setValue(limit)
            self.ba2_main_value.setText(str(value))
            self.ba2_main_value.setStyleSheet("color: #FF0000; font-weight: bold;")
            # Set bar to red when over limit
            self.ba2_main_progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #FF0000;
                    border-radius: 5px;
                    background-color: #2b2b2b;
                }
                QProgressBar::chunk {
                    background-color: #FF0000;
                    border-radius: 3px;
                }
            """)
            return
        
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
        """Update the texture BA2 bar - green until max, then red"""
        if value > limit:
            self.ba2_texture_progress.setValue(limit)
            self.ba2_texture_value.setText(str(value))
            self.ba2_texture_value.setStyleSheet("color: #FF0000; font-weight: bold;")
            # Set bar to red when over limit
            self.ba2_texture_progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #FF0000;
                    border-radius: 5px;
                    background-color: #2b2b2b;
                }
                QProgressBar::chunk {
                    background-color: #FF0000;
                    border-radius: 3px;
                }
            """)
            return
        
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
    
    def clear_content(self):
        """Clear the content area"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_ba2_info(self):
        """Show BA2 information view"""
        self.logger.debug("User navigated to BA2 Info tab")
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
        
        self.info_replacements_main = QLabel("--")
        self.info_replacements_texture = QLabel("--")
        replacements_layout = QHBoxLayout()
        replacements_layout.addWidget(QLabel("Vanilla Replacements: (not counted)"), 2)
        replacements_layout.addWidget(self.info_replacements_main, 1)
        replacements_layout.addWidget(self.info_replacements_texture, 1)
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
        warning_layout.setSpacing(2)
        warning_layout.setContentsMargins(0, 10, 0, 0)
        
        warning1_layout = QHBoxLayout()
        warning1_layout.setContentsMargins(0, 0, 0, 0)
        warning1 = QLabel("⚠ Exceeding 255 Main BA2 files will cause the game to crash on startup.")
        warning1.setStyleSheet("color: #FF0000; font-weight: bold;")
        warning1_layout.addWidget(warning1)
        warning1_layout.addStretch()
        warning_layout.addLayout(warning1_layout)
        
        warning2_layout = QHBoxLayout()
        warning2_layout.setContentsMargins(0, 0, 0, 0)
        warning2 = QLabel("⚠ Exceeding 254 Texture BA2 files will cause graphical corruption in your game.")
        warning2.setStyleSheet("color: #FF0000; font-weight: bold;")
        warning2_layout.addWidget(warning2)
        warning2_layout.addStretch()
        warning_layout.addLayout(warning2_layout)
        
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
        1. User sees list of all BA2 mods with checkboxes
        2. Checkboxes show current state: checked (green) = extracted, unchecked = packed BA2
        3. User toggles checkboxes to select mods for extraction/restoration
        4. User clicks 'Apply Changes' to execute the operations
        5. Checkbox appearance updates to reflect new state
        
        STATE TRACKING:
        - self.mod_ba2_state: dict mapping mod_name -> {'main': bool, 'texture': bool}
        - Tracks extraction state for each BA2 type independently
        - Used to detect changes: if checkbox state != tracked state, operation is needed
        """
        self.logger.debug("User navigated to Manage Mods tab")
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
        # New layout: Mod Name | Main BA2 (checkbox) | Texture BA2 (checkbox) | Merge (checkbox) | Nexus Link
        list_label = QLabel("Available BA2 Mods:")
        manage_layout.addWidget(list_label)
        
        self.mod_list = QTableWidget()
        self.mod_list.setColumnCount(5)
        self.mod_list.setHorizontalHeaderLabels(["Mod Name", "Main BA2", "Texture BA2", "Merge", "Nexus Link"])
        self.mod_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mod_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.mod_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.mod_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.mod_list.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Set fixed width for checkbox columns to enable centering
        self.mod_list.setColumnWidth(1, 80)
        self.mod_list.setColumnWidth(2, 80)
        self.mod_list.setColumnWidth(3, 60)
        self.mod_list.verticalHeader().setVisible(False)
        self.mod_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.mod_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Disable default item hover to avoid single-cell highlight confusion
        # We rely on row selection for visual feedback
        self.mod_list.setStyleSheet("""
            QTableWidget::item:hover { background-color: transparent; }
            QTableWidget::item:selected { background-color: #0078D7; color: white; }
        """)
        
        manage_layout.addWidget(self.mod_list, 1)
        
        # === ACTION BUTTON ===
        # Single button applies all checkbox changes at once
        # Logic: compares current checkbox state with tracked state, performs necessary operations
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        merge_selected_btn = QPushButton("Merge Selected Mods")
        merge_selected_btn.setMaximumWidth(200)
        merge_selected_btn.clicked.connect(self.merge_selected_mods)
        button_layout.addWidget(merge_selected_btn)
        
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
        
        self.cc_table = QTableWidget()
        self.cc_table.setColumnCount(2)
        self.cc_table.setHorizontalHeaderLabels(["Status", "Creation Club Content"])
        self.cc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.cc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.cc_table.setColumnWidth(0, 60)
        self.cc_table.verticalHeader().setVisible(False)
        self.cc_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.cc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        cc_layout.addWidget(self.cc_table, 1)
        
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
        
        cc_widget.setLayout(cc_layout)
        self.content_layout.addWidget(cc_widget)
        
        # Load CC list
        self.load_cc_list()
    
    def show_settings(self):
        """Show settings view"""
        self.logger.debug("User navigated to Settings tab")
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
        
        instructions = QLabel(
            "Please open Mod Organizer 2 and configure it to manage a Fallout 4 installation on your system, "
            "then restart this application. Use the controls below to set required paths."
        )
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
        # Auto-detect Archive2 only if MO2 is configured
        mo2_mods_dir = self.config.get("mo2_mods_dir", "")
        if not current_archive2 and mo2_mods_dir and os.path.exists(mo2_mods_dir):
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
        
        # Debug Logging Checkbox
        self.debug_logging_checkbox = QCheckBox("Enable Debug Logging (for troubleshooting)")
        self.debug_logging_checkbox.setChecked(self.config.get("debug_logging", False))
        form_layout.addRow("Debug Logging:", self.debug_logging_checkbox)
        settings_group.setLayout(form_layout)
        settings_layout.addWidget(settings_group)
        
        # Status
        self.settings_status = QTextEdit()
        self.settings_status.setReadOnly(True)
        # Reduced height by approx 2 lines (was 160, now 120 or less depending on font)
        # Actually, user asked to shrink by 2 lines. 160 is quite tall.
        # Let's try 100.
        self.settings_status.setMaximumHeight(100)
        # Removed "Configuration Status:" label as requested
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
        
        # Utility buttons group
        utils_group = QGroupBox("Diagnostic Tools")
        utils_layout = QVBoxLayout()
        
        # Enable FO4 debug logging button
        fo4_debug_btn = QPushButton("Enable Fallout 4 Debug Logging")
        fo4_debug_btn.clicked.connect(self.enable_fo4_debug_logging)
        fo4_debug_btn.setToolTip("Enables Papyrus script logging and additional debug output in Fallout 4")
        utils_layout.addWidget(fo4_debug_btn)
        
        # Bundle logs button
        bundle_logs_btn = QPushButton("Bundle All Logs to ZIP")
        bundle_logs_btn.clicked.connect(self.bundle_logs_to_zip)
        bundle_logs_btn.setToolTip("Creates a zip file containing ba2-manager.log, MO2 logs, and FO4 logs")
        utils_layout.addWidget(bundle_logs_btn)
        
        utils_group.setLayout(utils_layout)
        settings_layout.addWidget(utils_group)
        
        settings_layout.addStretch()
        settings_widget.setLayout(settings_layout)
        self.content_layout.addWidget(settings_widget)
    
    def safe_set_text(self, widget_name: str, text: str) -> None:
        """Safely set text on a widget that might have been deleted"""
        try:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if widget:
                    widget.setText(text)
        except RuntimeError:
            # Widget has been deleted (C++ object gone)
            pass

    def safe_set_style(self, widget_name: str, style: str) -> None:
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
                self.safe_set_text(
                    'info_status',
                    "Please open Mod Organizer 2 and configure it to manage a Fallout 4 installation on your system, then restart this application."
                )
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
            self.safe_set_text('info_main_texture', str(counts.get("main_textures", 0)))
            
            # DLC
            self.safe_set_text('info_dlc_main', str(counts["dlc"]))
            self.safe_set_text('info_dlc_texture', str(counts.get("dlc_textures", 0)))
            
            # Creation Club
            self.safe_set_text('info_cc_main', str(counts["creation_club"]))
            self.safe_set_text('info_cc_texture', str(counts.get("creation_club_textures", 0)))
            
            # Creation Store Mods
            self.safe_set_text('info_creation_store_main', str(counts["creation_store"]))
            self.safe_set_text('info_creation_store_texture', str(counts.get("creation_store_textures", 0)))
            
            # Mod BA2s
            self.safe_set_text('info_mods_main', str(counts["mod_main"]))
            self.safe_set_text('info_mods_texture', str(counts.get("mod_textures", 0)))
            
            # Replacements with separate main/texture counts
            self.safe_set_text('info_replacements_main', str(counts.get("replacement_main", 0)))
            self.safe_set_text('info_replacements_texture', str(counts.get("replacement_textures", 0)))
            
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
        Load and populate the mod list with separate Main and Texture BA2 checkboxes.
        
        Table layout:
        - Column 0: Mod Name (display only)
        - Column 1: Main BA2 (checkbox if mod has main BA2, empty otherwise)
        - Column 2: Texture BA2 (checkbox if mod has texture BA2, empty otherwise)
        - Column 3: Merge (checkbox - select mods to merge together)
        - Column 4: Nexus Link (clickable link if available)
        
        Checkbox states:
        - Unchecked (empty): Not extracted / BA2 is present
        - Checked (white): Selected to be extracted
        - Green checked: Already extracted / in backup only
        """
        try:
            mods = self.ba2_handler.list_ba2_mods()
            self.mod_list.setRowCount(0)  # Clear table
            # Track extraction state per mod: {mod_name: {'main': bool, 'texture': bool}}
            self.mod_ba2_state = {}
            
            for i, mod in enumerate(mods):
                self.mod_list.insertRow(i)
                mod_key = mod.mod_name
                
                # Initialize state tracking for this mod
                self.mod_ba2_state[mod_key] = {
                    'main': mod.main_extracted,
                    'texture': mod.texture_extracted
                }
                
                # === COLUMN 0: MOD NAME ===
                size_mb = mod.total_size / 1024 / 1024
                mod_name_item = QTableWidgetItem(f"{mod.mod_name} ({size_mb:.1f} MB)")
                mod_name_item.setData(Qt.ItemDataRole.UserRole, mod_key)
                mod_name_item.setFlags(mod_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.mod_list.setItem(i, 0, mod_name_item)
                
                # === COLUMN 1: MAIN BA2 CHECKBOX ===
                if mod.has_main_ba2:
                    # Create centered checkbox widget
                    main_widget = CenteredCheckBox()
                    main_widget.set_extracted(mod.main_extracted)
                    self.mod_list.setCellWidget(i, 1, main_widget)
                
                # === COLUMN 2: TEXTURE BA2 CHECKBOX ===
                if mod.has_texture_ba2:
                    # Create centered checkbox widget
                    texture_widget = CenteredCheckBox()
                    texture_widget.set_extracted(mod.texture_extracted)
                    self.mod_list.setCellWidget(i, 2, texture_widget)
                
                # === COLUMN 3: MERGE CHECKBOX ===
                # Always show merge checkbox for mods with BA2s
                if mod.has_main_ba2 or mod.has_texture_ba2:
                    merge_widget = CenteredCheckBox()
                    merge_widget.set_extracted(False)  # Start unchecked
                    self.mod_list.setCellWidget(i, 3, merge_widget)
                
                # === COLUMN 4: NEXUS LINK ===
                if mod.nexus_url:
                    link_label = QLabel(f'<a href="{mod.nexus_url}">Nexus Page</a>')
                    link_label.setOpenExternalLinks(True)
                    link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.mod_list.setCellWidget(i, 4, link_label)
            
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
        
        Gets all available CC packages from ba2_handler and populates the table
        with checkable items showing which are currently active.
        """
        try:
            fo4_path = self.config.get("fo4_path", "")
            if not fo4_path:
                self.cc_status.setText(
                    "Please open Mod Organizer 2 and configure it to manage a Fallout 4 installation on your system, then restart this application."
                )
                return
            
            # Ensure master backup exists (created on first load)
            self.ba2_handler.create_cc_master_backup(fo4_path)
            
            # Get CC packages with their active status
            cc_packages = self.ba2_handler.get_cc_packages(fo4_path)
            
            self.cc_table.setRowCount(0)
            self.cc_table.setRowCount(len(cc_packages))
            
            for row, (plugin_id, display_name, is_active) in enumerate(cc_packages):
                # Status Column (CenteredCheckBox)
                status_widget = CenteredCheckBox()
                # Treat "Active" as "Extracted" (Green) and "Inactive" as "Packed" (Grey)
                status_widget.set_extracted(is_active)
                # Store plugin ID in the widget for retrieval
                status_widget.setProperty("plugin_id", plugin_id)
                self.cc_table.setCellWidget(row, 0, status_widget)
                
                # Name Column
                name_item = QTableWidgetItem(display_name)
                name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.cc_table.setItem(row, 1, name_item)
            
            # Update status
            active_count = sum(1 for _, _, is_active in cc_packages if is_active)
            self.cc_status.setText(f"Found {len(cc_packages)} CC package(s)\n{active_count} currently enabled")
        except Exception as e:
            self.cc_status.setText(f"Error loading CC packages: {str(e)}")
    
    def apply_mod_changes(self):
        """
        Execute extraction/restoration based on checkbox states for individual BA2 files.
        
        NEW WORKFLOW (per BA2 file):
        - User checks box -> item turns GREY (pending extraction)
        - User clicks "Apply Changes" -> extraction happens
        - After completion -> item turns GREEN (extraction complete)
        - User unchecks box -> item turns BLACK (restored/normal)
        
        BACKUP LOGIC:
        - If EITHER main or texture checkbox is checked, back up the entire mod for restore
        - If ONLY ONE is already green (extracted) and the OTHER is checked, don't create new backup
        - The backup from the first extraction covers both BA2 files
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
                # Get mod name from column 0
                name_item = self.mod_list.item(i, 0)
                if not name_item:
                    continue
                
                mod_name = name_item.data(Qt.ItemDataRole.UserRole)
                if not mod_name:
                    continue
                
                # Get main and texture checkbox widgets (columns 1 and 2)
                main_widget = self.mod_list.cellWidget(i, 1)
                texture_widget = self.mod_list.cellWidget(i, 2)
                
                # Check if checkboxes are present and their current states
                main_checked = main_widget and main_widget.isChecked()
                texture_checked = texture_widget and texture_widget.isChecked()
                
                # Get tracked states (what was extracted before this operation)
                mod_state = self.mod_ba2_state.get(mod_name, {})
                main_was_extracted = mod_state.get('main', False)
                texture_was_extracted = mod_state.get('texture', False)
                
                # Determine if we need to back up (before any extraction)
                need_backup = False
                if (main_checked and not main_was_extracted) or (texture_checked and not texture_was_extracted):
                    need_backup = True
                
                # === PROCESS MAIN BA2 ===
                if main_widget:
                    if main_checked != main_was_extracted:
                        changes_made = True
                        
                        if main_checked:
                            # User checked -> EXTRACT main BA2
                            # Only backup if this is the first file being extracted for this mod
                            should_backup = need_backup and not texture_was_extracted
                            
                            if self.ba2_handler.extract_mod_ba2(mod_name, "main", should_backup):
                                main_widget.set_extracted(True)
                                self.mod_ba2_state[mod_name]['main'] = True
                                extracted_count += 1
                            else:
                                main_widget.setCheckState(Qt.CheckState.Unchecked)
                                failed_count += 1
                        else:
                            # User unchecked -> RESTORE main BA2
                            if self.ba2_handler.restore_mod_ba2(mod_name, "main"):
                                main_widget.set_extracted(False)
                                self.mod_ba2_state[mod_name]['main'] = False
                                restored_count += 1
                            else:
                                main_widget.setCheckState(Qt.CheckState.Checked)
                                failed_count += 1
                
                # === PROCESS TEXTURE BA2 ===
                if texture_widget:
                    if texture_checked != texture_was_extracted:
                        changes_made = True
                        
                        if texture_checked:
                            # User checked -> EXTRACT texture BA2
                            # Only backup if main wasn't extracted yet (if we're extracting both, main handled backup)
                            should_backup = need_backup and not main_was_extracted
                            
                            if self.ba2_handler.extract_mod_ba2(mod_name, "texture", should_backup):
                                texture_widget.set_extracted(True)
                                self.mod_ba2_state[mod_name]['texture'] = True
                                extracted_count += 1
                            else:
                                texture_widget.setCheckState(Qt.CheckState.Unchecked)
                                failed_count += 1
                        else:
                            # User unchecked -> RESTORE texture BA2
                            if self.ba2_handler.restore_mod_ba2(mod_name, "texture"):
                                texture_widget.set_extracted(False)
                                self.mod_ba2_state[mod_name]['texture'] = False
                                restored_count += 1
                            else:
                                texture_widget.setCheckState(Qt.CheckState.Checked)
                                failed_count += 1
            
            # === REPORT RESULTS ===
            if not changes_made:
                self.mod_status.setText("No changes to apply.")
            else:
                message = "Operation complete!"
                if extracted_count > 0:
                    message += f"\nExtracted {extracted_count} BA2 file(s)."
                if restored_count > 0:
                    message += f"\nRestored {restored_count} BA2 file(s)."
                if failed_count > 0:
                    message += f"\nFailed operations: {failed_count}. Check logs."
                self.mod_status.setText(message)
                
                # Refresh the mod list to show updated extraction states
                self.load_mod_list()
                
                # Refresh the BA2 count bar
                self.refresh_ba2_count()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.mod_status.setText(f"Error applying changes: {e}")
        finally:
            self.setEnabled(True)
    
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
            for row in range(self.cc_table.rowCount()):
                widget = self.cc_table.cellWidget(row, 0)
                if isinstance(widget, CenteredCheckBox):
                    widget.setChecked(True)
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
            for row in range(self.cc_table.rowCount()):
                widget = self.cc_table.cellWidget(row, 0)
                if isinstance(widget, CenteredCheckBox):
                    widget.setChecked(False)
            self.apply_cc_changes()

    def apply_cc_changes(self):
        """Apply changes to Fallout4.ccc based on checkbox states"""
        try:
            fo4_path = self.config.get("fo4_path", "")
            if not fo4_path:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Please open Mod Organizer 2 and configure it to manage a Fallout 4 installation on your system, then restart this application."
                )
                return
                
            enabled_plugins = []
            
            # Gather all checked items
            for row in range(self.cc_table.rowCount()):
                widget = self.cc_table.cellWidget(row, 0)
                if isinstance(widget, CenteredCheckBox) and widget.isChecked():
                    # Property stores the full filename (e.g. "ccbgsfo4001.esl")
                    plugin_filename = widget.property("plugin_id")
                    if plugin_filename:
                        enabled_plugins.append(plugin_filename)
            
            # Call handler to write the file
            if self.ba2_handler.write_ccc_file(fo4_path, enabled_plugins):
                self.cc_status.setText(f"Successfully updated Fallout4.ccc with {len(enabled_plugins)} active plugins.")
                
                # Update visual state to reflect applied changes
                for row in range(self.cc_table.rowCount()):
                    widget = self.cc_table.cellWidget(row, 0)
                    if isinstance(widget, CenteredCheckBox):
                        # If it was checked (enabled), it is now "Extracted" (Active/Green)
                        # If it was unchecked (disabled), it is now "Packed" (Inactive/Grey)
                        widget.set_extracted(widget.isChecked())
                
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
            
            # Read custom mod_directory from ModOrganizer.ini if it exists
            mods_path = self.read_mod_directory_from_ini(mo2_root)
            if not mods_path:
                # Default to standard mods folder if not configured
                mods_path = str(Path(mo2_root) / "mods")
            
            backup_path = str(Path(mo2_root) / "BA2_Manager_Backups")
            
            self.settings_mo2_display.setText(mods_path)
            self.config.set("mo2_mods_dir", mods_path)
            self.config.set("backup_dir", backup_path)
            
            # Attempt to auto-detect Fallout 4 path from MO2 config
            fo4_path = self.detect_fo4_from_mo2(mo2_root)
            if fo4_path:
                self.config.set("fo4_path", fo4_path)
            
            # Auto-detect Archive2.exe using comprehensive search
            detected_archive2 = None
            
            # 1) Check MO2 root directory first (portable installs)
            mo2_archive2 = Path(mo2_root) / "Archive2.exe"
            if mo2_archive2.exists():
                detected_archive2 = str(mo2_archive2)
            
            # 2) Check Fallout 4 Tools directory if FO4 was detected
            if not detected_archive2 and fo4_path:
                fo4_archive2 = Path(fo4_path) / "Tools" / "Archive2" / "Archive2.exe"
                if fo4_archive2.exists():
                    detected_archive2 = str(fo4_archive2)
            
            # 3) Fall back to registry detection
            if not detected_archive2:
                detected_archive2 = self.detect_archive2_from_registry()
            
            # Update UI and config if found
            if detected_archive2:
                self.settings_archive2_display.setText(detected_archive2)
                self.config.set("archive2_path", detected_archive2)
            
            # Reinitialize BA2Handler with new MO2 path
            self.ba2_handler = BA2Handler(
                archive2_path=self.config.get("archive2_path") or None,
                mo2_dir=mods_path,
                log_file=self.config.get("log_file", "ba2-manager.log")
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
                log_file=self.config.get("log_file", "ba2-manager.log")
            )
            
            self.update_settings_status()
            QMessageBox.information(self, "Success", f"Archive2.exe found!\nPath: {file_path}")
        elif file_path:
            QMessageBox.warning(self, "Error", "Please select Archive2.exe")
    
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
            self.logger.debug(f"Registry detection failed: {e}")
            return None
        return None

    def read_mod_directory_from_ini(self, mo2_root: str) -> Optional[str]:
        """
        Read custom mod_directory setting from ModOrganizer.ini
        
        Returns:
            Custom mod directory path if configured, None otherwise
        """
        try:
            ini_path = Path(mo2_root) / "ModOrganizer.ini"
            if not ini_path.exists():
                return None
                
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().startswith('mod_directory='):
                        # Extract value after mod_directory=
                        value = line.strip().split('=', 1)[1]
                        
                        # Handle @ByteArray(path) format
                        if value.startswith('@ByteArray(') and value.endswith(')'):
                            # Extract content between parenthesis
                            path_str = value[11:-1]
                            # Replace double backslashes
                            path_str = path_str.replace('\\\\', '\\')
                            # If path is relative, make it absolute from mo2_root
                            if not Path(path_str).is_absolute():
                                path_str = str(Path(mo2_root) / path_str)
                            return path_str
                        else:
                            # Standard format
                            value = value.strip()
                            # If path is relative, make it absolute from mo2_root
                            if not Path(value).is_absolute():
                                value = str(Path(mo2_root) / value)
                            return value
        except Exception as e:
            self.logger.warning(f"Error reading mod_directory from ModOrganizer.ini: {e}")
            return None
        return None

    def detect_fo4_from_mo2(self, mo2_root: str) -> Optional[str]:
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
            self.logger.debug(f"Error reading ModOrganizer.ini: {e}")
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

        status_lines.append("")
        status_lines.append("Note: You must select the ModOrganizer.exe location before using BA2 features.")
        
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
                    "debug_logging": self.debug_logging_checkbox.isChecked(),
                })
            except RuntimeError:
                # Widgets have been deleted
                return
            
            # Reinitialize BA2Handler with new paths
            mo2_mods_dir = self.config.get("mo2_mods_dir", "mods")
            archive2_path = self.config.get("archive2_path", "")
            log_file = self.config.get("log_file", "ba2-manager.log")
            
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
    
    def enable_fo4_debug_logging(self):
        """Enable Fallout 4 debug logging by modifying Fallout4Custom.ini"""
        try:
            # Get Fallout 4 Documents folder
            documents = Path.home() / "Documents" / "My Games" / "Fallout4"
            if not documents.exists():
                QMessageBox.warning(
                    self,
                    "FO4 Folder Not Found",
                    f"Fallout 4 documents folder not found at:\n{documents}\n\nPlease launch Fallout 4 at least once to create this folder."
                )
                return
            
            custom_ini = documents / "Fallout4Custom.ini"
            
            # Read existing content or create new
            if custom_ini.exists():
                with open(custom_ini, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            # Settings to add/update
            settings_to_add = {
                "[Papyrus]": [
                    "bEnableLogging=1",
                    "bEnableTrace=1",
                    "bLoadDebugInformation=1"
                ],
                "[General]": [
                    "sStartingConsoleCommand="
                ],
                "[Archive]": [
                    "bInvalidateOlderFiles=1",
                    "sResourceDataDirsFinal="
                ]
            }
            
            # Process each section
            for section, settings in settings_to_add.items():
                if section not in content:
                    # Add new section
                    content += f"\n{section}\n"
                    for setting in settings:
                        content += f"{setting}\n"
                else:
                    # Update existing section
                    for setting in settings:
                        key = setting.split('=')[0]
                        if key not in content:
                            # Find section and add setting
                            section_pos = content.find(section)
                            next_section = content.find("\n[", section_pos + 1)
                            if next_section == -1:
                                next_section = len(content)
                            insert_pos = next_section
                            content = content[:insert_pos] + f"{setting}\n" + content[insert_pos:]
            
            # Write updated content
            with open(custom_ini, 'w') as f:
                f.write(content)
            
            # Create Logs directory if it doesn't exist
            logs_dir = documents / "Logs" / "Script"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            QMessageBox.information(
                self,
                "Debug Logging Enabled",
                f"Fallout 4 debug logging has been enabled!\n\n"
                f"Modified: {custom_ini}\n\n"
                f"Logs will be saved to:\n{logs_dir}\n\n"
                f"Note: You must restart Fallout 4 for changes to take effect."
            )
            self.logger.info(f"Enabled FO4 debug logging in {custom_ini}")
            
        except Exception as e:
            self.logger.error(f"Error enabling FO4 debug logging: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to enable Fallout 4 debug logging:\n\n{str(e)}"
            )
    
    def bundle_logs_to_zip(self):
        """Bundle all relevant logs into a zip file in the MO2 folder"""
        try:
            mo2_mods_dir = self.config.get("mo2_mods_dir", "")
            if not mo2_mods_dir or not os.path.exists(mo2_mods_dir):
                QMessageBox.warning(
                    self,
                    "MO2 Not Configured",
                    "Please configure Mod Organizer 2 path in Settings first."
                )
                return
            
            # Determine MO2 root (parent of mods folder)
            mo2_root = Path(mo2_mods_dir).parent
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = mo2_root / f"BA2_Manager_Logs_{timestamp}.zip"
            
            files_added = []
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. BA2 Manager log (current directory)
                ba2_log = Path("ba2-manager.log")
                if ba2_log.exists():
                    zipf.write(ba2_log, "ba2-manager.log")
                    files_added.append("ba2-manager.log")
                
                # 2. MO2 logs
                mo2_logs = mo2_root / "logs"
                if mo2_logs.exists():
                    for log_file in mo2_logs.glob("*.log"):
                        zipf.write(log_file, f"MO2_logs/{log_file.name}")
                        files_added.append(f"MO2: {log_file.name}")
                    for log_file in mo2_logs.glob("*.txt"):
                        zipf.write(log_file, f"MO2_logs/{log_file.name}")
                        files_added.append(f"MO2: {log_file.name}")
                
                # 3. Fallout 4 logs
                fo4_docs = Path.home() / "Documents" / "My Games" / "Fallout4"
                if fo4_docs.exists():
                    # Papyrus logs
                    papyrus_logs = fo4_docs / "Logs" / "Script"
                    if papyrus_logs.exists():
                        for log_file in papyrus_logs.glob("*.log"):
                            zipf.write(log_file, f"FO4_Papyrus/{log_file.name}")
                            files_added.append(f"FO4 Papyrus: {log_file.name}")
                    
                    # F4SE logs
                    f4se_logs = fo4_docs / "F4SE"
                    if f4se_logs.exists():
                        for log_file in f4se_logs.glob("*.log"):
                            zipf.write(log_file, f"F4SE_logs/{log_file.name}")
                            files_added.append(f"F4SE: {log_file.name}")
                    
                    # Crash logs
                    crash_logs = fo4_docs / "CrashLogs"
                    if crash_logs.exists():
                        for log_file in crash_logs.glob("*.log"):
                            zipf.write(log_file, f"Crash_logs/{log_file.name}")
                            files_added.append(f"Crash: {log_file.name}")
            
            if not files_added:
                QMessageBox.warning(
                    self,
                    "No Logs Found",
                    "No log files were found to bundle."
                )
                zip_filename.unlink()  # Delete empty zip
                return
            
            # Show success message
            files_list = "\n".join([f"  • {f}" for f in files_added[:10]])
            if len(files_added) > 10:
                files_list += f"\n  ... and {len(files_added) - 10} more"
            
            QMessageBox.information(
                self,
                "Logs Bundled",
                f"Successfully bundled {len(files_added)} log files!\n\n"
                f"Saved to:\n{zip_filename}\n\n"
                f"Files included:\n{files_list}"
            )
            self.logger.info(f"Bundled {len(files_added)} logs to {zip_filename}")
            
        except Exception as e:
            self.logger.error(f"Error bundling logs: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to bundle logs:\n\n{str(e)}"
            )
    
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
                if not item:
                    continue
                    
                mod_name = item.data(Qt.ItemDataRole.UserRole)
                if not mod_name:
                    continue
                
                # Check if currently extracted using the new state tracking
                mod_state = self.mod_ba2_state.get(mod_name, {})
                is_extracted = mod_state.get('main', False) or mod_state.get('texture', False)
                
                if is_extracted:
                    if self.ba2_handler.restore_mod(mod_name):
                        # Update UI for Main BA2
                        main_widget = self.mod_list.cellWidget(i, 1)
                        if main_widget:
                            main_widget.set_extracted(False)
                        
                        # Update UI for Texture BA2
                        texture_widget = self.mod_list.cellWidget(i, 2)
                        if texture_widget:
                            texture_widget.set_extracted(False)
                        
                        # Update state tracking
                        self.mod_ba2_state[mod_name] = {'main': False, 'texture': False}
                        
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
        
        # Create a larger dialog to prevent text wrapping
        dialog = QDialog(self)
        dialog.setWindowTitle("MIT License")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(license_text)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_merge_ba2s(self):
        """Display the Merge CC BA2s view"""
        self.clear_content()
        
        # Create widget
        merge_widget = QWidget()
        merge_layout = QVBoxLayout()
        merge_layout.setSpacing(15)
        
        # Title and description
        title = QLabel("Merge Creation Club BA2 Archives")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        merge_layout.addWidget(title)
        
        description = QLabel(
            "Merge all Creation Club BA2 files into two unified archives to reduce your BA2 count.\n\n"
            "This process will:\n"
            "• Backup all original CC BA2 files\n"
            "• Extract and combine them into CCMerged - Main.ba2 and CCMerged - Textures.ba2\n"
            "• Create a dummy ESL file (CCMerged.esl) to load the merged archives\n"
            "• Delete the original individual CC BA2 files\n\n"
            "The merge can be reversed at any time using the Restore button."
        )
        description.setWordWrap(True)
        merge_layout.addWidget(description)
        
        # Status group
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()
        
        self.merge_status_label = QLabel("Checking status...")
        status_layout.addWidget(self.merge_status_label)
        
        status_group.setLayout(status_layout)
        merge_layout.addWidget(status_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.merge_btn = QPushButton("Merge CC BA2s")
        self.merge_btn.setMinimumHeight(50)
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.merge_btn.clicked.connect(self.perform_merge)
        button_layout.addWidget(self.merge_btn)
        
        self.restore_btn = QPushButton("Restore Original CC BA2s")
        self.restore_btn.setMinimumHeight(50)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.restore_btn.clicked.connect(self.perform_restore)
        button_layout.addWidget(self.restore_btn)
        
        merge_layout.addLayout(button_layout)
        
        # Progress and output
        self.merge_output = QTextEdit()
        self.merge_output.setReadOnly(True)
        self.merge_output.setMaximumHeight(200)
        merge_layout.addWidget(self.merge_output)
        
        # Warning
        warning = QLabel(
            "⚠ WARNING: This is an advanced operation. Make sure you have backups of your Data folder.\n"
            "The merge will modify your Fallout 4 Data directory and cannot be undone without the backup."
        )
        warning.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        warning.setWordWrap(True)
        merge_layout.addWidget(warning)
        
        merge_layout.addStretch()
        merge_widget.setLayout(merge_layout)
        self.content_layout.addWidget(merge_widget)
        
        # Update status
        self.update_merge_status()
    
    def update_merge_status(self):
        """Update the merge status display"""
        fo4_path = self.config.get("fo4_path", "")
        if not fo4_path or not self.ba2_handler:
            self.merge_status_label.setText("❌ Fallout 4 path not configured")
            self.merge_btn.setEnabled(False)
            self.restore_btn.setEnabled(False)
            return
        
        status = self.ba2_handler.get_cc_merge_status(fo4_path)
        
        if "error" in status:
            self.merge_status_label.setText(f"❌ Error: {status['error']}")
            self.merge_btn.setEnabled(False)
            self.restore_btn.setEnabled(False)
            return
        
        is_merged = status.get("is_merged", False)
        cc_count = status.get("individual_cc_count", 0)
        merged_files = status.get("merged_files", [])
        backups = status.get("available_backups", [])
        
        if is_merged:
            status_text = f"✓ CC BA2s are currently MERGED\n\n"
            status_text += f"Merged files: {', '.join(merged_files)}\n\n"
            status_text += f"Individual CC BA2s remaining: {cc_count}\n\n"
            if backups:
                status_text += f"Available backups: {len(backups)}\n"
                for backup in backups:
                    status_text += f"  • {backup['name']} ({backup['cc_count']} BA2s)\n"
            
            self.merge_status_label.setText(status_text)
            self.merge_btn.setEnabled(False)
            self.restore_btn.setEnabled(len(backups) > 0)
        else:
            status_text = f"Individual CC BA2s: {cc_count}\n\n"
            if cc_count > 0:
                status_text += "CC BA2s are NOT merged. You can merge them to reduce your BA2 count."
            else:
                status_text += "No CC BA2s found to merge."
            
            self.merge_status_label.setText(status_text)
            self.merge_btn.setEnabled(cc_count > 0)
            self.restore_btn.setEnabled(False)
    
    def perform_merge(self):
        """Perform the CC BA2 merge operation"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Merge",
            "Are you sure you want to merge all Creation Club BA2 files?\n\n"
            "This will:\n"
            "• Backup your original CC BA2 files\n"
            "• Create merged archives\n"
            "• Delete the original BA2 files\n\n"
            "You can restore them later if needed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI during operation
        self.setEnabled(False)
        self.merge_output.clear()
        self.merge_output.append("Starting merge operation...\n")
        QApplication.processEvents()
        
        try:
            fo4_path = self.config.get("fo4_path", "")
            result = self.ba2_handler.merge_cc_ba2s(fo4_path)
            
            if result.get("success"):
                self.merge_output.append("✓ Merge completed successfully!\n")
                self.merge_output.append(f"\n📊 Statistics:")
                self.merge_output.append(f"  • Original BA2 count: {result.get('original_count', 0)}")
                
                # Calculate total merged archives
                texture_count = result.get('texture_archive_count', 1)
                total_merged = 1 + texture_count  # 1 main + N textures
                self.merge_output.append(f"  • Merged into: {total_merged} archives")
                self.merge_output.append(f"  • BA2 reduction: {result.get('original_count', 0) - total_merged} fewer archives")
                
                if texture_count > 1:
                    self.merge_output.append(f"\n⚠️ Texture archives split into {texture_count} files (4GB limit per archive)")
                
                if result.get("merged_main"):
                    self.merge_output.append(f"\n✓ Created: {os.path.basename(result['merged_main'])}")
                
                # Handle multiple texture archives
                merged_textures = result.get("merged_textures", [])
                if isinstance(merged_textures, list):
                    for tex_path in merged_textures:
                        self.merge_output.append(f"✓ Created: {os.path.basename(tex_path)}")
                elif merged_textures:  # Backward compatibility for single string
                    self.merge_output.append(f"✓ Created: {os.path.basename(merged_textures)}")
                
                if result.get("dummy_esl"):
                    self.merge_output.append(f"✓ Created: {os.path.basename(result['dummy_esl'])}")
                
                self.merge_output.append(f"\n📁 Backup saved to:")
                self.merge_output.append(f"  {result.get('backup_path', 'N/A')}")
                self.merge_output.append(f"\n🗑️ Removed {result.get('original_count', 0)} original CC BA2 files")
                
                self.merge_output.append(f"\n💡 Note: Duplicate files across BA2s were automatically deduplicated.")
                self.merge_output.append(f"   The merged archives contain only unique files.")
                
                QMessageBox.information(
                    self,
                    "Merge Complete",
                    f"Successfully merged {result.get('original_count', 0)} CC BA2 files into {total_merged} archives!"
                )
                
                # Update status
                self.update_merge_status()
                # Refresh BA2 count
                self.refresh_ba2_count()
            else:
                error = result.get("error", "Unknown error")
                self.merge_output.append(f"\n❌ Merge failed: {error}")
                QMessageBox.critical(
                    self,
                    "Merge Failed",
                    f"Failed to merge CC BA2 files:\n\n{error}"
                )
        except Exception as e:
            self.merge_output.append(f"\n❌ Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during merge:\n\n{str(e)}"
            )
        finally:
            self.setEnabled(True)
    
    def perform_restore(self):
        """Restore original CC BA2 files from backup"""
        fo4_path = self.config.get("fo4_path", "")
        status = self.ba2_handler.get_cc_merge_status(fo4_path)
        backups = status.get("available_backups", [])
        
        if not backups:
            QMessageBox.warning(self, "No Backup", "No backup found to restore from.")
            return
        
        # Use the most recent backup (first in list)
        backup_path = backups[0]["path"]
        backup_count = backups[0]["cc_count"]
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore {backup_count} original CC BA2 files?\n\n"
            "This will:\n"
            "• Remove the merged archives\n"
            "• Restore all individual CC BA2 files\n"
            "• Delete the backup folder\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI during operation
        self.setEnabled(False)
        self.merge_output.clear()
        self.merge_output.append("Starting restore operation...\n")
        QApplication.processEvents()
        
        try:
            result = self.ba2_handler.restore_cc_ba2s(backup_path, fo4_path)
            
            if result.get("success"):
                self.merge_output.append("✓ Restore completed successfully!\n")
                self.merge_output.append(f"\nRestored {result.get('restored_count', 0)} CC BA2 files")
                
                removed = result.get("removed_merged", [])
                if removed:
                    self.merge_output.append(f"\n✓ Removed merged files:")
                    for filename in removed:
                        self.merge_output.append(f"  • {filename}")
                
                self.merge_output.append(f"\n✓ Deleted backup folder")
                
                QMessageBox.information(
                    self,
                    "Restore Complete",
                    f"Successfully restored {result.get('restored_count', 0)} original CC BA2 files!"
                )
                
                # Update status
                self.update_merge_status()
                # Refresh BA2 count
                self.refresh_ba2_count()
            else:
                error = result.get("error", "Unknown error")
                self.merge_output.append(f"\n❌ Restore failed: {error}")
                QMessageBox.critical(
                    self,
                    "Restore Failed",
                    f"Failed to restore CC BA2 files:\n\n{error}"
                )
        except Exception as e:
            self.merge_output.append(f"\n❌ Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during restore:\n\n{str(e)}"
            )
        finally:
            self.setEnabled(True)
    
    def merge_selected_mods(self):
        """Merge selected mods' BA2 files into unified archives"""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get selected mods (those with merge checkbox checked)
        selected_mods = []
        for i in range(self.mod_list.rowCount()):
            merge_widget = self.mod_list.cellWidget(i, 3)  # Column 3 is Merge checkbox
            if merge_widget and merge_widget.isChecked():
                mod_name_item = self.mod_list.item(i, 0)
                if mod_name_item:
                    mod_name = mod_name_item.data(Qt.ItemDataRole.UserRole)
                    selected_mods.append(mod_name)
        
        if not selected_mods:
            QMessageBox.warning(
                self,
                "No Mods Selected",
                "Please select at least one mod to merge by checking the 'Merge' checkbox."
            )
            return
        
        # Prompt for ESL name
        esl_name, ok = QInputDialog.getText(
            self,
            "Merge Mods",
            f"Enter name for merged archives (without extension):\n\n"
            f"Selected mods ({len(selected_mods)}):\n" + "\n".join(f"  • {m}" for m in selected_mods[:10]) +
            (f"\n  ... and {len(selected_mods) - 10} more" if len(selected_mods) > 10 else ""),
            text="CustomMerged"
        )
        
        if not ok or not esl_name.strip():
            return
        
        esl_name = esl_name.strip()
        
        # Confirm merge
        reply = QMessageBox.question(
            self,
            "Confirm Merge",
            f"Merge {len(selected_mods)} mod(s) into '{esl_name}'?\n\n"
            f"This will:\n"
            f"• Backup all original BA2 files\n"
            f"• Combine them into unified archives\n"
            f"• Create {esl_name}.esl plugin\n"
            f"• Delete original BA2 files\n\n"
            f"This process can be reversed later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI during operation
        self.setEnabled(False)
        self.mod_status.clear()
        self.mod_status.append("Starting merge operation...\n")
        QApplication.processEvents()
        
        try:
            fo4_path = self.config.get("fo4_path", "")
            result = self.ba2_handler.merge_custom_ba2s(selected_mods, fo4_path, esl_name)
            
            if result.get("success"):
                self.mod_status.append("✓ Merge completed successfully!\n")
                self.mod_status.append(f"\n📊 Statistics:")
                self.mod_status.append(f"  • Mods merged: {len(selected_mods)}")
                
                texture_count = result.get('texture_archive_count', 1)
                total_merged = (1 if result.get('merged_main') else 0) + texture_count
                self.mod_status.append(f"  • Archives created: {total_merged}")
                
                if result.get("merged_main"):
                    self.mod_status.append(f"\n✓ Created: {os.path.basename(result['merged_main'])}")
                
                merged_textures = result.get("merged_textures", [])
                if isinstance(merged_textures, list):
                    for tex_path in merged_textures:
                        self.mod_status.append(f"✓ Created: {os.path.basename(tex_path)}")
                
                if result.get("dummy_esl"):
                    self.mod_status.append(f"✓ Created: {os.path.basename(result['dummy_esl'])}")
                
                self.mod_status.append(f"\n📁 Backup: {result.get('backup_path', 'N/A')}")
                
                QMessageBox.information(
                    self,
                    "Merge Complete",
                    f"Successfully merged {len(selected_mods)} mod(s) into {total_merged} archive(s)!"
                )
                
                # Refresh mod list
                self.load_mod_list()
                self.refresh_ba2_count()
            else:
                error = result.get("error", "Unknown error")
                self.mod_status.append(f"\n❌ Merge failed: {error}")
                QMessageBox.critical(
                    self,
                    "Merge Failed",
                    f"Failed to merge mods:\n\n{error}"
                )
        except Exception as e:
            self.mod_status.append(f"\n❌ Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during merge:\n\n{str(e)}"
            )
        finally:
            self.setEnabled(True)
