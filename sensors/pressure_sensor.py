from datetime import datetime
from typing import override
from sensors.sensor import Sensor
import time
import numpy as np
import threading
from sensors.humidity_sensor import HumiditySensor
from sensors.temperature_sensor import TemperatureSensor
from logger.logger import Logger


class PressureSensor(Sensor):
    def __init__(self, name="Pressure Sensor", unit="hPa", min_value=950, max_value=1050, frequency=1, logger = None):
        super().__init__(name, unit, min_value, max_value, frequency)
        self.temperature_dependency = True
        self.humidity_dependency = True
        self.temperature_sensor = None
        self.humidity_sensor = None

        self.logger = logger
        if self.logger:
            # self.logger.set_sensor_context(self.sensor_id, self.name, self.unit)
            self.register_callback(self.logger.log_reading)

    @override
    def read_value(self):
        now = datetime.now()

        # ustaw temperature z czujnika, domyslnie 20
        temperature = self.temperature_sensor.get_last_value() if self.temperature_sensor else 20

        # ustaw wilgotnosc z czujnika, domyslnie 1000
        humidity = self.humidity_sensor.get_last_value() if self.humidity_sensor else 1000

        # Korekta ciśnienia na podstawie temperatury i wilgotności
        adjustment = (temperature - 20) * 0.3 + (humidity - 50) * 0.2
        base_value = np.random.uniform(self.min_value, self.max_value)
        value = round(np.clip(base_value + adjustment, self.min_value, self.max_value), 1)

        self.last_value = value
        self.last_read_time = now

        for callback in self._callbacks:
            callback(self.sensor_id, now, self.last_value, self.unit)

        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} = {self.last_value}{self.unit}")

    # Funkcja do odczytu ciśnienia na podstawie temperatury i wilgotności
    def read_loop(self):
        interval = 1 / self.frequency
        while not self.stop_thread:
            self.read_value()
            time.sleep(interval)

    # Funkcja ustawiajaca referencje sensora temperatury
    def set_temperature_sensor(self, temperature_sensor):
        self.temperature_sensor = temperature_sensor

    # Funkcja ustawiajaca referencje sensora wilgotnosci
    def set_humidity_sensor(self, humidity_sensor):
        self.humidity_sensor = humidity_sensor

    # Funkcja uruchamiająca wątek z odczytem ciśnienia
    def start_reading(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")
        if self.reading_thread and self.reading_thread.is_alive():
            return

        self.stop_thread = False
        self.reading_thread = threading.Thread(target=self.read_loop)
        self.reading_thread.start()

    # Funkcja wyłączająca wątek z odczytem ciśnienia
    def stop_reading(self):
        self.stop_thread = True
        if self.reading_thread:
            self.reading_thread.join()


if __name__ == '__main__':
    logger = Logger("../config.json")
    tempSensor = TemperatureSensor()
    humiditySensor = HumiditySensor()
    pressureSensor = PressureSensor(logger=logger)

    humiditySensor.set_temperature_sensor(tempSensor)
    pressureSensor.set_temperature_sensor(tempSensor)
    pressureSensor.set_humidity_sensor(humiditySensor)

    sensors = [tempSensor, humiditySensor, pressureSensor]

    # Włączenie czujników
    for s in sensors:
        s.start()

    # Wlaczenie odczytu
    for s in sensors:
        s.start_reading()
        time.sleep(1)

    time.sleep(10)

    # Zakończenie odczytów
    for s in sensors:
        s.stop_reading()
        s.stop()

