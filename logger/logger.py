import os
import csv
import json
import zipfile
from datetime import datetime
from typing import Optional, Dict, Iterator

class Logger:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            config = json.load(f)

        self.log_dir = config.get("log_dir", "./logs")
        self.filename_pattern = config.get("filename_pattern", "sensors_%Y%m%d.csv")
        self.buffer_size = config.get("buffer_size", 100)
        self.rotate_every_hours = config.get("rotate_every_hours", 24)
        self.max_size_mb = config.get("max_size_mb", 10)
        self.rotate_after_lines = config.get("rotate_after_lines", None)
        self.retention_days = config.get("retention_days", 30)

        self.buffer = []
        self.current_file = None
        self.current_writer = None
        self.current_filename = None
        self.current_file_open_time = None
        self.line_count = 0

        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "archive"), exist_ok=True)

    def start(self):
        self.current_file_open_time = datetime.now()
        self.current_filename = os.path.join(self.log_dir, self.current_file_open_time.strftime(self.filename_pattern))
        is_new = not os.path.exists(self.current_filename)

        self.current_file = open(self.current_filename, "a", newline="", encoding="utf-8")
        self.current_writer = csv.writer(self.current_file)

        if is_new:
            self.current_writer.writerow(["sensor_id", "timestamp", "value", "unit"])
        self.line_count = 0

    def stop(self):
        self._flush()
        if self.current_file:
            self.current_file.close()
            self._check_rotation(force=False)

    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str):
        self.buffer.append([sensor_id, timestamp.isoformat(), value, unit])
        if len(self.buffer) >= self.buffer_size:
            self._flush()

        self._check_rotation()

    def _flush(self):
        if not self.current_writer:
            return
        self.current_writer.writerows(self.buffer)
        self.line_count += len(self.buffer)
        self.buffer.clear()
        self.current_file.flush()

    def _check_rotation(self, force=False):
        now = datetime.now()
        duration = (now - self.current_file_open_time).total_seconds()
        file_size_mb = os.path.getsize(self.current_filename) / (1024 * 1024)

        rotate = False
        if force:
            rotate = True
        elif duration >= self.rotate_every_hours * 3600:
            rotate = True
        elif file_size_mb >= self.max_size_mb:
            rotate = True
        elif self.rotate_after_lines and self.line_count >= self.rotate_after_lines:
            rotate = True

        if rotate:
            self._rotate()

    def _rotate(self):
        self._flush()
        self.current_file.close()

        archive_name = self.current_filename.replace(self.log_dir, os.path.join(self.log_dir, "archive")) + ".zip"
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.current_filename, arcname=os.path.basename(self.current_filename))

        os.remove(self.current_filename)
        self.start()
        self._clean_old_archives()

    def _clean_old_archives(self):
        archive_dir = os.path.join(self.log_dir, "archive")
        now = datetime.now()
        for filename in os.listdir(archive_dir):
            filepath = os.path.join(archive_dir, filename)
            if not filename.endswith(".zip"):
                continue
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (now - file_time).days > self.retention_days:
                os.remove(filepath)

    def read_logs(self, start: datetime, end: datetime, sensor_id: Optional[str] = None) -> Iterator[Dict]:
        def parse_row(row):
            try:
                ts = datetime.fromisoformat(row[0])
                return {
                    "timestamp": ts,
                    "sensor_id": row[1],
                    "value": float(row[2]),
                    "unit": row[3]
                }
            except:
                return None

        def process_file(filepath):
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader, None)
                for row in reader:
                    data = parse_row(row)
                    if data and start <= data["timestamp"] <= end:
                        if sensor_id is None or data["sensor_id"] == sensor_id:
                            yield data

        for fname in os.listdir(self.log_dir):
            if fname.endswith(".csv"):
                yield from process_file(os.path.join(self.log_dir, fname))

        for zipname in os.listdir(os.path.join(self.log_dir, "archive")):
            if not zipname.endswith(".zip"):
                continue
            with zipfile.ZipFile(os.path.join(self.log_dir, "archive", zipname), 'r') as zipf:
                for name in zipf.namelist():
                    with zipf.open(name) as f:
                        lines = f.read().decode('utf-8').splitlines()
                        reader = csv.reader(lines)
                        headers = next(reader, None)
                        for row in reader:
                            data = parse_row(row)
                            if data and start <= data["timestamp"] <= end:
                                if sensor_id is None or data["sensor_id"] == sensor_id:
                                    yield data
