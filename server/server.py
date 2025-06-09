import socket
import json
import logging
import sys
import os
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from network.config import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class NetworkServer:
    def __init__(self, port=None):
        config = load_config().get("server", {})
        self.port = port or config.get("port", 9000)
        self.callback = None
        self.running = threading.Event()

    def register_callback(self, callback):
        self.callback = callback

    def start(self) -> None:
        self.running.set()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", self.port))
            s.listen()
            s.settimeout(1.0)  # timeout na accept, by móc sprawdzić flagę running
            logger.info(f"Serwer nasłuchuje na porcie {self.port}...")

            while self.running.is_set():
                try:
                    client_socket, addr = s.accept()
                    logger.info(f"Połączenie od {addr}")
                    threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Błąd serwera: {e}")
                    break

    def stop(self):
        self.running.clear()

    def _handle_client(self, client_socket) -> None:
        buffer = b""
        while True:
            try:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    message, buffer = buffer.split(b"\n", 1)
                    try:
                        data = self._deserialize(message)
                        logger.info("Odebrano dane:")
                        for key, value in data.items():
                            logger.info(f"  {key}: {value}")
                        if self.callback:
                            self.callback(data)
                        client_socket.sendall(b"ACK\n")
                    except Exception as e:
                        logger.error(f"Błąd dekodowania JSON: {e}")
            except Exception as e:
                logger.error(f"Błąd połączenia: {e}")
                break

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8"))

if __name__ == "__main__":
    config = load_config()
    server_config = config.get("server", {})
    port = server_config.get("port", 9000)

    server = NetworkServer(port)
    logger.info(f"Serwer nasłuchuje na porcie {port}...")

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Zatrzymanie serwera (KeyboardInterrupt)")
        server.stop()
    finally:
        logger.info("Serwer został zamknięty.")
