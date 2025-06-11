import sys
import os
import socket
import time
from datetime import datetime
import json

# Dodaj ścieżkę do katalogu głównego
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensors.temperature_sensor import TemperatureSensor
from sensors.humidity_sensor import HumiditySensor
from sensors.pressure_sensor import PressureSensor
from sensors.light_sensor import LightSensor
from logger.logger import Logger

def main():
    # Pobierz nazwę klienta z argumentów, domyślnie "default_client"
    client_name = sys.argv[1] if len(sys.argv) > 1 else "default_client"

    # Inicjalizacja sensorów
    temp = TemperatureSensor()
    hum = HumiditySensor()
    press = PressureSensor()
    light = LightSensor()

    # Ustaw zależności
    hum.set_temperature_sensor(temp)
    press.set_temperature_sensor(temp)
    press.set_humidity_sensor(hum)

    sensors = [temp, hum, press, light]

    # Włącz sensory i uruchom odczyty w tle
    for s in sensors:
        s.start()
        s.start_reading()  # uruchom wątek odczytu

    # Inicjalizacja loggera
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    logger = Logger(config_path=os.path.abspath(config_path))
    logger.start()

    server_ip = "127.0.0.1"
    server_port = 9000

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((server_ip, server_port))
            print(f"[CLIENT] Połączono z serwerem {server_ip}:{server_port}")

            while True:
                for s in sensors:
                    value = s.get_last_value()
                    timestamp = datetime.now()

                    sensor_id = f"({client_name}){s.name}"

                    # Logowanie lokalne
                    logger.log_reading(sensor_id=sensor_id, timestamp=timestamp, value=value, unit=s.unit)

                    # Wysyłka danych do serwera
                    payload = {
                        "sensor_id": sensor_id,
                        "timestamp": timestamp.isoformat(),
                        "value": value,
                        "unit": s.unit
                    }
                    msg = (json.dumps(payload) + "\n").encode("utf-8")
                    try:
                        sock.sendall(msg)
                    except (BrokenPipeError, ConnectionResetError) as e:
                        print(f"[CLIENT] Połączenie z serwerem przerwane: {e}")
                        return  # możesz też dodać ponowne łączenie jeśli chcesz

                    time.sleep(0.2)  # krótkie opóźnienie między sensorami
                time.sleep(1)  # opóźnienie pomiędzy cyklami odczytu

    except KeyboardInterrupt:
        print("\n[CLIENT] Zamykanie...")

    except Exception as e:
        print(f"[CLIENT] Błąd: {e}")

    finally:
        # Zatrzymaj wątki odczytów i sensory
        for s in sensors:
            s.stop_reading()
            s.stop()
        logger.stop()
        print("[CLIENT] Zamknięto wszystkie procesy.")

if __name__ == "__main__":
    main()
