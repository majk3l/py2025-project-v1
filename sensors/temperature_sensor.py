import time
import threading
from datetime import datetime
import numpy as np
from sensors.sensor import Sensor
from logger.logger import Logger

class TemperatureSensor(Sensor):
    def __init__(self, name="Temperature Sensor", unit="°C", min_value=-15, max_value=35, frequency=1, logger=None):
        super().__init__(name, unit, min_value, max_value, frequency)

        self.logger = logger
        if self.logger:
            # self.logger.set_sensor_context(self.sensor_id, self.name, self.unit)
            self.register_callback(self.logger.log_reading)

        self.temperature_ranges = {
            'winter': {'night': (-15, -5), 'day': (-5, 2), 'evening': (-10, -3)},
            'spring': {'night': (0, 5), 'day': (10, 18), 'evening': (6, 12)},
            'summer': {'night': (15, 20), 'day': (25, 35), 'evening': (18, 25)},
            'autumn': {'night': (5, 10), 'day': (10, 18), 'evening': (7, 12)}
        }

    def get_season(self, month):
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'

    def get_time_period(self, hour):
        if 0 <= hour < 8:
            return 'night'
        elif 8 <= hour < 16:
            return 'day'
        else:
            return 'evening'

    def read_value(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")

        now = datetime.now()
        season = self.get_season(now.month)
        period = self.get_time_period(now.hour)

        temp_min, temp_max = self.temperature_ranges[season][period]
        value = round(np.random.uniform(temp_min, temp_max))

        self.last_value = value
        self.last_read_time = now

        for callback in self._callbacks:
            callback(self.sensor_id, now, value, self.unit)

        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} = {self.last_value}{self.unit}")

    def read_loop(self):
        interval = 1 / self.frequency
        while not self.stop_thread:
            self.read_value()
            time.sleep(interval)

    def start_reading(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")
        if self.reading_thread and self.reading_thread.is_alive():
            return
        self.stop_thread = False
        self.reading_thread = threading.Thread(target=self.read_loop)
        self.reading_thread.start()

    def stop_reading(self):
        self.stop_thread = True
        if self.reading_thread:
            self.reading_thread.join()

if __name__ == '__main__':
    logger = Logger("../config.json")

    tempSensor = TemperatureSensor(logger=logger)
    tempSensor.start()
    tempSensor.start_reading()

    time.sleep(10)

    tempSensor.stop_reading()
    tempSensor.stop()