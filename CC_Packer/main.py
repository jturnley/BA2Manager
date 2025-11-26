import sys
import os
import logging
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from merger import CCMerger

class MergeWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger, fo4_path, archive2_path):
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path
        self.archive2_path = archive2_path

    def run(self):
        try:
            result = self.merger.merge_cc_content(self.fo4_path, self.archive2_path, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Merge completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))

class RestoreWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger, fo4_path):
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path

    def run(self):
        try:
            result = self.merger.restore_backup(self.fo4_path, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Restore completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.merger = CCMerger()
        self.init_ui()
        self.detect_paths()

    def init_ui(self):
        self.setWindowTitle("CC Packer")
        self.setMinimumSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header = QLabel("CC Packer")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # FO4 Path
        layout.addWidget(QLabel("Fallout 4 Directory:"))
        fo4_layout = QHBoxLayout()
        self.fo4_input = QLineEdit()
        fo4_btn = QPushButton("Browse")
        fo4_btn.clicked.connect(self.browse_fo4)
        fo4_layout.addWidget(self.fo4_input)
        fo4_layout.addWidget(fo4_btn)
        layout.addLayout(fo4_layout)

        # Archive2 Path
        layout.addWidget(QLabel("Archive2.exe Path:"))
        a2_layout = QHBoxLayout()
        self.a2_input = QLineEdit()
        a2_btn = QPushButton("Browse")
        a2_btn.clicked.connect(self.browse_archive2)
        a2_layout.addWidget(self.a2_input)
        a2_layout.addWidget(a2_btn)
        layout.addLayout(a2_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.merge_btn = QPushButton("Merge CC Content")
        self.merge_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.merge_btn.clicked.connect(self.start_merge)
        
        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.restore_btn.clicked.connect(self.start_restore)
        
        btn_layout.addWidget(self.merge_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def log(self, message):
        self.log_output.append(message)

    def detect_paths(self):
        # Try to detect FO4
        # Common paths
        common_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4",
            r"C:\Program Files\Steam\steamapps\common\Fallout 4",
            r"D:\SteamLibrary\steamapps\common\Fallout 4"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.fo4_input.setText(path)
                self.check_archive2(path)
                break

    def check_archive2(self, fo4_path):
        # Check default location
        default_a2 = os.path.join(fo4_path, "Tools", "Archive2", "Archive2.exe")
        if os.path.exists(default_a2):
            self.a2_input.setText(default_a2)
            self.log("Archive2.exe found automatically.")
        else:
            self.log("Archive2.exe not found in default location.")
            reply = QMessageBox.question(self, "Archive2 Missing", 
                                       "Archive2.exe was not found in the default location.\n\n"
                                       "It is required to pack BA2 files. It comes with the Creation Kit.\n\n"
                                       "Would you like to open the Steam page for the Creation Kit?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("steam://install/1946160")

    def browse_fo4(self):
        path = QFileDialog.getExistingDirectory(self, "Select Fallout 4 Directory")
        if path:
            self.fo4_input.setText(path)
            self.check_archive2(path)

    def browse_archive2(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Archive2.exe", filter="Executables (*.exe)")
        if path:
            self.a2_input.setText(path)

    def start_merge(self):
        fo4 = self.fo4_input.text()
        a2 = self.a2_input.text()

        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return
        if not a2 or not os.path.exists(a2):
            QMessageBox.warning(self, "Error", "Invalid Archive2 path.")
            return

        self.merge_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.log("Starting merge process...")
        
        self.worker = MergeWorker(self.merger, fo4, a2)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def start_restore(self):
        fo4 = self.fo4_input.text()
        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return

        self.merge_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.log("Starting restore process...")

        self.worker = RestoreWorker(self.merger, fo4)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        self.merge_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", message)
            self.log(f"DONE: {message}")
        else:
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
