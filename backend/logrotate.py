
import os
import shutil
from datetime import datetime

LOG_FILE = "log.txt"
ARCHIVE_DIR = "log_archive"
MAX_SIZE_MB = 1

def rotate_log_if_needed():
    if not os.path.exists(LOG_FILE):
        return

    size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
    if size_mb < MAX_SIZE_MB:
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_name = f"log_{timestamp}.txt"
    shutil.move(LOG_FILE, os.path.join(ARCHIVE_DIR, archived_name))
