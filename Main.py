import time
from datetime import datetime

from Czujniki import TemperatureSensor, HumiditySensor, PressureSensor, AirQualitySensor

def main():
    temp_sensor = TemperatureSensor(sensor_id=1)
    hum_sensor = HumiditySensor(sensor_id=2, temperature_sensor=temp_sensor)
    aq_sensor = AirQualitySensor(sensor_id=4, humidity_sensor = hum_sensor)

    sensors = [
        temp_sensor, hum_sensor,
        PressureSensor(sensor_id=3),
        aq_sensor
    ]

    for i in range(5):
        now = datetime.now()

        next_hour = (now.hour + i) % 24 # Obliczanie godziny z uwzględnieniem iteracji, ale nie przekraczaj 23
        formatted_time = f"{next_hour:02d}:00"   # Zmiana formatu na 0i:00

        print(f"=== Odczyty {i+1}, godzina pomiaru: {formatted_time} ===")
        for sensor in sensors:
            value = sensor.read_value()
            if isinstance(sensor, AirQualitySensor):
                print(f"{sensor.name}: {value:.2f} {sensor.unit} | {sensor.get_air_quality_level()}")
            else:
                print(f"{sensor.name}: {value:.2f} {sensor.unit}")
            if hasattr(sensor, 'przyczyna'):
                print(f"    | {sensor.przyczyna}")
        print()
        time.sleep(1)

if __name__ == "__main__":
    main()