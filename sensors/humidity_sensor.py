from datetime import datetime
from typing import override
from sensors.sensor import Sensor
import time
import numpy as np
import threading
from sensors.temperature_sensor import TemperatureSensor
from logger.logger import Logger


class HumiditySensor(Sensor):
    def __init__(self, name="Humidity Sensor", unit="%", min_value=0, max_value=100, frequency=1, logger=None):
        super().__init__(name, unit, min_value, max_value, frequency)
        self.temperature_dependency = True
        self.temperature_sensor = None

        self.logger = logger
        if self.logger:
            # self.logger.set_sensor_context(self.sensor_id, self.name, self.unit)
            self.register_callback(self.logger.log_reading)

    @override
    def read_value(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")

        now = datetime.now()
        temperature = self.temperature_sensor.get_last_value() if self.temperature_sensor else 20
        adjustment = np.clip((30 - temperature) * 1.5, 0, 100) if self.temperature_dependency else 0

        base_value = np.random.uniform(40, 70)
        value = round(np.clip(base_value + np.random.normal(0, 5) + adjustment, 0, 100), 1)

        self.last_value = value
        self.last_read_time = now

        for callback in self._callbacks:
            callback(self.sensor_id, now, self.last_value, self.unit)

        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} = {value}{self.unit}")

    # funkcja ktora odczytuje wilgotnosc na podstawie temperatury
    def read_loop(self):
        interval = 1 / self.frequency
        while not self.stop_thread:
            self.read_value()
            time.sleep(interval)

    # Funkcja ustawiajaca referencje sensora temperatury
    def set_temperature_sensor(self, temperature_sensor):
        self.temperature_sensor = temperature_sensor

    # funkcja ktora uruchamia watek z odczytywaniem wilgotnosci
    def start_reading(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")
        if self.reading_thread and self.reading_thread.is_alive():
            return
        self.stop_thread = False
        self.reading_thread = threading.Thread(target=self.read_loop)
        self.reading_thread.start()

    # funkcja wylaczenia watku z odczytywaniem wilgotnosci
    def stop_reading(self):
        self.stop_thread = True
        if self.reading_thread:
            self.reading_thread.join()


if __name__ == '__main__':
    logger = Logger("../config.json")
    tempSensor = TemperatureSensor()
    humiditySensor = HumiditySensor(logger=logger)
    humiditySensor.set_temperature_sensor(tempSensor)

    # wlaczenie czujnika wilgotnosci i temperatur, odczytywanie pomiarow , po 5s zakoncz pomiary i wylacz oba czujniki
    tempSensor.start()
    humiditySensor.start()

    tempSensor.start_reading()
    time.sleep(1)
    humiditySensor.start_reading()

    time.sleep(10)

    humiditySensor.stop_reading()
    tempSensor.stop_reading()
    humiditySensor.stop()
    tempSensor.stop()



