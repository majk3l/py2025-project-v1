# server_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from server.server import NetworkServer  # zakładamy że masz ten moduł
from network.config import load_config


class ServerThread(threading.Thread):
    def __init__(self, port, data_queue, status_callback):
        super().__init__(daemon=True)
        self.port = port
        self.data_queue = data_queue
        self.status_callback = status_callback
        self._running = threading.Event()
        self._running.set()

    def run(self):
        try:
            server = NetworkServer(self.port)
            server.register_callback(self.data_queue.put)  # callback do przekazywania danych
            self.status_callback("Nasłuchiwanie")
            server.start_forever(self._running)  # zmodyfikuj server.py by wspierał to
        except Exception as e:
            self.status_callback(f"Błąd: {e}")

    def stop(self):
        self._running.clear()


class GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serwer TCP - GUI")
        self.data_queue = queue.Queue()
        self.sensor_data = defaultdict(lambda: deque(maxlen=500))  # bufor danych per czujnik

        self._build_ui()

        self.server_thread = None
        self.updating_enabled = False  # <- to musi być PRZED update_ui()
        self.update_ui()

    def _build_ui(self):
        # Górny panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(control_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(control_frame, width=6)
        self.port_entry.insert(0, str(load_config().get("server_port", 9000)))
        self.port_entry.pack(side="left", padx=5)

        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_server)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_server, state="disabled")
        self.stop_button.pack(side="left")

        # Tabela czujników
        self.tree = ttk.Treeview(self.root, columns=("sensor", "value", "unit", "timestamp", "avg1h", "avg12h"),
                                 show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Pasek statusu
        self.status = tk.StringVar()
        self.status.set("Serwer zatrzymany")
        status_bar = ttk.Label(self.root, textvariable=self.status, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")

    def update_ui(self):
        try:
            if self.updating_enabled:
                while not self.data_queue.empty():
                    raw = self.data_queue.get()
                    self.process_data(raw)
            else:
                # Opróżniamy kolejkę, żeby nie zapełniała się w tle
                while not self.data_queue.empty():
                    self.data_queue.get_nowait()
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd przetwarzania danych: {e}")

        self.root.after(2000, self.update_ui)

    def process_data(self, data):
        sensor_id = data.get("sensor_id", "unknown")
        value = data.get("value", 0)
        unit = data.get("unit", "")
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            # Jeśli timestamp jest w formacie ISO8601 (np. '2025-06-09T15:00:00'), konwertuj tak:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()

        self.sensor_data[sensor_id].append((timestamp, value))

        avg1h = self._calculate_average(sensor_id, timedelta(hours=1))
        avg12h = self._calculate_average(sensor_id, timedelta(hours=12))

        # Aktualizacja tabeli
        row = (sensor_id, round(value, 2), unit, timestamp.strftime("%Y-%m-%d %H:%M:%S"),
               round(avg1h, 2) if avg1h else "", round(avg12h, 2) if avg12h else "")

        if self.tree.exists(sensor_id):
            self.tree.item(sensor_id, values=row)
        else:
            self.tree.insert("", "end", iid=sensor_id, values=row)

    def _calculate_average(self, sensor_id, interval):
        now = datetime.now()
        values = [v for t, v in self.sensor_data[sensor_id] if now - t <= interval]
        if not values:
            return None
        return sum(values) / len(values)

    def start_server(self):
        if self.server_thread is None:
            try:
                port = int(self.port_entry.get())
                self.server_thread = ServerThread(port, self.data_queue, self.set_status)
                self.server_thread.start()
                self.set_status("Nasłuchiwanie")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się uruchomić serwera: {e}")
                return

        # Niezależnie od tego, czy serwer już był, wznawiamy aktualizacje
        self.updating_enabled = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
            self.set_status("Serwer zatrzymany")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.updating_enabled = False  # zatrzymaj aktualizacje

    def set_status(self, text):
        self.status.set(text)


if __name__ == "__main__":
    root = tk.Tk()
    app = GuiApp(root)
    root.mainloop()
