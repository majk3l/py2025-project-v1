from typing import override
from sensors.sensor import Sensor
from datetime import datetime
import threading
import time
import numpy as np
from logger.logger import Logger

class LightSensor(Sensor):
    def __init__(self, name="Light Sensor", unit="lx", min_value=0, max_value=10000, frequency=1, logger = None):
        super().__init__(name, unit, min_value, max_value, frequency)

        self.logger = logger
        if self.logger:
            # self.logger.set_sensor_context(self.sensor_id, self.name, self.unit)
            self.register_callback(self.logger.log_reading)

        # zakres lumenow w zaleznosci od pory dnia
        self.light_ranges = {
            'night': (0, 500),
            'day': (1000, 2000),
            'evening': (500, 1000)
        }

    # funkcja zwracajaca pore dnia w zaleznosci od aktualnej godziny
    def get_part_of_day(self, hour):
        if hour in [23,0,1,2,3,4,5]:
            return 'night'
        elif hour in [6,7,8,9,10,11,12,13,14,15,16,17]:
            return 'day'
        else:
            return 'evening'

    @override
    def read_value(self):
        now = datetime.now()
        part_of_day = self.get_part_of_day(now.hour)

        light_min, light_max = self.light_ranges[part_of_day]
        value = round(np.random.uniform(light_min, light_max), 1)

        self.last_value = value
        self.last_read_time = now

        for callback in self._callbacks:
            callback(self.sensor_id, now, self.last_value, self.unit)

        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} = {self.last_value}{self.unit}")

    # funkcja ktora odczytuje ilosc lumenow
    def read_loop(self):
        interval = 1 / self.frequency
        while not self.stop_tread:
            self.read_value()
            time.sleep(interval)

    # funkcja ktora uruchamia watek z odczytywaniem temperatur
    def start_reading(self):
        # sprawdz czy sensor nie jest wlaczony
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")
        # sprawdz czy watek juz istnieje oraz jest aktywny a jezeli tak to nie uruchamiaj po raz drugi.
        if self.reading_thread and self.reading_thread.is_alive():
            return

        self.stop_tread = False
        self.reading_thread = threading.Thread(target=self.read_loop)
        self.reading_thread.start()

    # funkcja wylaczenia watku z odczytywaniem temperatury
    def stop_reading(self):
        self.stop_tread = True
        # upewnia zeby zablokowac wykonanie dalszego kodu w glownym watku dopoki wskazany watek sie nie zakonczy.
        if self.reading_thread:
            self.reading_thread.join()

if __name__ == "__main__":
    logger = Logger("../config.json")
    lightSensor = LightSensor(logger=logger)

    # Włączenie czujników i rozpoczęcie odczytu
    lightSensor.start()

    lightSensor.start_reading()
    time.sleep(10)

    # Zakończenie odczytów
    lightSensor.stop_reading()
    lightSensor.stop()


