import os
import time
import datetime
from qt.core import QTimer, QEventLoop, QObject, pyqtSignal, QFileSystemWatcher
from tempfile import gettempdir
from shutil import move
from typing import Optional
from pathlib import Path
from .CustomLogger import CustomLogger

class FileWaiter(QObject):
    file_found = pyqtSignal(str)
    timeout_reached = pyqtSignal()
  

    def __init__(self, folder, extension, interval_ms, timeout_ms):
        super().__init__()
        self.folder = folder
        self.extension = extension
        self.start_time = time.time()

        self.watcher = QFileSystemWatcher([folder])
        self.watcher.directoryChanged.connect(self.check_for_file)

        self.scan_timer = QTimer()
        self.scan_timer.setInterval(interval_ms)
        self.scan_timer.timeout.connect(self.check_for_file)
        self.scan_timer.start()

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.setInterval(timeout_ms)
        self.timeout_timer.timeout.connect(self.handle_timeout)
        self.timeout_timer.start()

    def check_for_file(self):
        self.extension = self.extension.lower()
        print(f"checking for {self.extension} in {self.folder}")
        for fname in os.listdir(self.folder):          
            if fname.lower().endswith(self.extension):
                full_path = os.path.join(self.folder, fname)
                if os.path.isfile(full_path):
                    created = os.path.getctime(full_path)
                    if created >= self.start_time :
                        self.file_found.emit(full_path)
                        self.cleanup()
                        print(full_path)
                        break
                    else :
                        createdString = datetime.datetime.fromtimestamp(created)       .strftime("%Y-%m-%d %H:%M:%S")
                        startString   = datetime.datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
                        CustomLogger.log_simple_string(f"Ignoring pre-existing file {full_path} {createdString} before {startString}")






    def handle_timeout(self):
        self.timeout_reached.emit()
        self.cleanup()

    def cleanup(self):
        self.scan_timer.stop()
        self.timeout_timer.stop()
        self.watcher.removePath(self.folder)
                                
def wait_for_file_qt(folder : str, extension : str,  interval_ms = 500, timeout_ms=300000) -> Optional[Path]:    # 300000 = 5 minutes
    loop = QEventLoop()
    waiter = FileWaiter(folder, extension, interval_ms , timeout_ms)

    result = {}

    def on_file_found(path):
        result['path'] = path
        loop.quit()
     
    def on_timeout():
        result['path'] = None
        loop.quit()


    waiter.file_found.connect(on_file_found)
    waiter.timeout_reached.connect(on_timeout)
    loop.exec_()

    file_path = result['path']
    if file_path :

        temp_path = os.path.join(gettempdir() , os.path.basename(file_path))
        print(f"Moving {file_path} to {temp_path}")
        move(file_path, temp_path)

        return Path(temp_path)
    else :
        return None


# Example usage
if __name__ == "__main__":
    folder_to_watch = "~/Downloads"
    extension = ".acsm"
    file_path = wait_for_file_qt(folder_to_watch, extension)
    print(f"Detected file: {file_path}")

 