import numpy as np
from datetime import datetime

class Sensor:
    _type_counters = {}  # Liczniki osobno dla każdego typu sensora

    def __init__(self, name, unit, min_value, max_value, frequency=1, active=False, last_value=None, start_time=None, last_read_time=None, logger=None):
        cls = self.__class__
        if cls not in Sensor._type_counters:
            Sensor._type_counters[cls] = 1
        else:
            Sensor._type_counters[cls] += 1

        self.sensor_id = Sensor._type_counters[cls]

        if frequency > 10:
            raise Exception("Maximum frequency is 10Hz!")

        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.frequency = frequency
        self.active = active
        self.last_value = last_value
        self.start_time = start_time
        self.last_read_time = last_read_time
        self.reading_thread = None
        self.stop_thread = False
        self._callbacks = []

        self.logger = logger
        if self.logger:
            self.logger.set_sensor_context(self.sensor_id, self.name, self.unit)
            self.logger.start()
            self.register_callback(self.logger.log_reading)

    def read_value(self):
        if not self.active:
            raise Exception(f"Sensor {self.name} is off.")

        now = datetime.now()
        value = round(np.random.uniform(self.min_value, self.max_value), 1)

        self.last_value = value
        self.last_read_time = now

        for callback in self._callbacks:
            callback(self.sensor_id, now, value, self.unit)

        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} = {value}{self.unit}")

    def calibrate(self, calibration_factor):
        if self.last_value is None:
            self.read_value()
        self.last_value *= calibration_factor
        return self.last_value

    def get_last_value(self):
        if self.last_value is None:
            self.read_value()
        return self.last_value

    def start(self):
        self.start_time = datetime.now()
        self.active = True

    def stop(self):
        self.active = False

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def __str__(self):
        return f"Sensor(id={self.sensor_id}, name={self.name}, unit={self.unit}, active={self.active})"

    @classmethod
    def reset_type_counters(cls):
        Sensor._type_counters = {}