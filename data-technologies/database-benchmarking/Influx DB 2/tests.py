# test_influx.py
import time
from faker import Faker
from influx_db_client import InfluxDBClient2

from datetime import datetime, timezone, timedelta
import random
import uuid

import warnings
from influxdb_client.client.warnings import MissingPivotFunction
warnings.simplefilter("ignore", MissingPivotFunction)

fake = Faker()


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res = fn(*args, **kwargs)
    end = time.perf_counter()
    return res, (end - start)


print("Creating InfluxDB client and buckets...")
influx = InfluxDBClient2(batch_size=100000)  # tune batch size
influx.create_buckets(
    retention_days_readings=0, retention_days_meta=0, retention_days_alerts=0
)
print("Buckets:", influx.get_all_buckets())

# ── CONFIG ──
D = 10  # devices
S = 10  # sensors per device
R = 100000  # readings per sensor
A = 5  # alerts per device

now = datetime.now(timezone.utc)


def insert():
    influx.force_flush()
    start_time = time.perf_counter()
    for i in range(1, D + 1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc = fake.city()
        st = random.choice(["online", "offline", "unknown"])

        device_id = uuid.uuid4()
        _, t = timed(influx.insert_device, str(device_id), name, loc, st)

        for j in range(1, S + 1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp", "hum", "press"])
            sensor_id = uuid.uuid4()

            _, t = timed(influx.insert_sensor, str(sensor_id), str(device_id), typ)

            for k in range(1, R + 1):
                # timestamp distribution similar to your ClickHouse script
                tstamp = now - timedelta(
                    days=random.randint(0, 10), minutes=k * random.random() * 5
                )
                val = random.random() * 100
                reading_id = uuid.uuid4()

                # batch insert
                _, t = timed(
                    influx.insert_reading,
                    str(reading_id),
                    str(sensor_id),
                    str(device_id),
                    val,
                    tstamp,
                )

        for _ in range(A):
            tstamp = now - timedelta(hours=random.random() * 24)
            atype = random.choice(["overheat", "disconnect", "low-battery"])
            desc = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            influx.insert_alert(str(alert_id), str(device_id), atype, tstamp, desc)

    influx.force_flush()
    end_time = time.perf_counter()
    print(f"Data insertion completed in {end_time - start_time:.2f} seconds")


def get_counts():
    counts = influx.get_counts()
    print(
        f"Devices: {counts['devices']}, Sensors: {counts['sensors']}, Readings: {counts['readings']}, Alerts: {counts['alerts']}"
    )


def execute_queries():
    print("Executing analytical queries...")

    avg_readings, t = timed(influx.get_avg_reading_per_device_per_day)
    print(f"Average readings per device per day query executed in {t:.2f} seconds")
    print(avg_readings.head(20))

    extremes, t = timed(influx.get_sensor_extremes_per_device)
    print(f"Sensor extremes per device query executed in {t:.2f} seconds")
    print(extremes.head(20))

    at, t = timed(influx.get_avg_time_between_readings)
    print(f"Average time between readings query executed in {t:.2f} seconds")
    print(at.head(20))


insert()
get_counts()
execute_queries()

