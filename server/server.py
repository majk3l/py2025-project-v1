import socket
import threading
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkServer:
    def __init__(self, port):
        self.port = port
        self.callbacks = []

    def register_callback(self, callback):
        """Dodaje callback, który będzie wywoływany przy otrzymaniu danych."""
        self.callbacks.append(callback)

    def _handle_client(self, client_socket):
        addr = client_socket.getpeername()
        logger.info(f"Obsługa klienta {addr} rozpoczęta")
        try:
            with client_socket:
                buffer = ""
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        logger.info(f"Połączenie z {addr} zakończone przez klienta")
                        break

                    buffer += data.decode('utf-8')
                    # Załóżmy, że wiadomości są rozdzielone nową linią
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            message = json.loads(line)
                            logger.info(f"Otrzymano od {addr}: {message}")
                            for cb in self.callbacks:
                                cb(message)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Niepoprawny JSON od {addr}: {line} - {e}")

        except Exception as e:
            logger.error(f"Błąd obsługi klienta {addr}: {e}")

    def start_forever(self, running_event) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", self.port))
            s.listen()
            s.settimeout(1.0)  # timeout, by móc przerwać pętlę
            logger.info(f"Serwer nasłuchuje na porcie {self.port}...")

            while running_event.is_set():
                try:
                    client_socket, addr = s.accept()
                    logger.info(f"Połączenie od {addr}")
                    threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
                except socket.timeout:
                    continue  # pozwala sprawdzać flagę running_event
                except Exception as e:
                    logger.error(f"Błąd serwera: {e}")
                    break
