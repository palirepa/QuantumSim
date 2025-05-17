import sys
import traceback

from PyQt6.QtWidgets import QApplication
from mw.mainWindow import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("Starting done. Application is ready.", flush=True)
    try:
        sys.exit(app.exec())
    except Exception:
        print("Exception caught:")
        traceback.print_exc()

if __name__ == '__main__':
    main()
