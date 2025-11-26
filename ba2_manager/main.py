"""Main entry point for BA2 Manager application"""

import sys
import traceback
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from ba2_manager.gui.main_window import MainWindow


def exception_hook(exctype, value, tb):
    """Global exception handler to log crashes"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    
    # Log to file
    try:
        with open("crash_log.txt", "a") as f:
            f.write("\n" + "="*50 + "\n")
            f.write(error_msg)
    except:
        pass
        
    logging.error("Unhandled exception:\n" + error_msg)
    
    # Try to show a message box if QApplication is active
    if QApplication.instance():
        try:
            QMessageBox.critical(None, "Critical Error", f"An unhandled exception occurred:\n{value}\n\nSee crash_log.txt for details.")
        except:
            pass

sys.excepthook = exception_hook


def main():
    """Run the BA2 Manager application"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("BA2 Manager")
    app.setApplicationVersion("2.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
