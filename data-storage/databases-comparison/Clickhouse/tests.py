import time
from faker import Faker
from clickhouse_client import ClickHouseClient

from datetime import datetime, timedelta
import random
import uuid

fake = Faker()


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res = fn(*args, **kwargs)
    end = time.perf_counter()
    return res, (end - start)

print("Creating ClickHouse client and schema...")
clickhouse_client = ClickHouseClient(batch_size=100000)
clickhouse_client.create_schema()
print("ClickHouse database and tables created:",
      clickhouse_client.get_all_tables())


# ── CONFIG ──
D = 10    # devices
S = 10    # sensors per device
R = 100000   # readings per sensor
A = 5    # alerts per device

now = datetime.utcnow()

# latency store

def insert():
    clickhouse_client.force_flush()
    start_time = time.perf_counter()
    for i in range(1, D+1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc = fake.city()
        st = random.choice(["online", "offline", "unknown"])

        device_id = uuid.uuid4()
        _, t = timed(clickhouse_client.insert_device,
                     str(device_id), name, loc, st)

        for j in range(1, S+1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp", "hum", "press"])
            sensor_id = uuid.uuid4()

            _, t = timed(clickhouse_client.insert_sensor,
                         sensor_id, device_id, typ)

            for k in range(1, R+1):
                tstamp = now - timedelta(days=random.randint(0, 10),
                                         minutes=k * random.random() * 5)
                val = random.random() * 100
                reading_id = uuid.uuid4()

                _, t = timed(clickhouse_client.insert_reading,
                             reading_id, sensor_id, device_id, val, tstamp)

        for _ in range(A):
            tstamp = now - timedelta(hours=random.random()*24)
            atype = random.choice(["overheat", "disconnect", "low-battery"])
            desc = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            clickhouse_client.insert_alert(
                alert_id, device_id, atype, tstamp, desc)

    clickhouse_client.force_flush()
    end_time = time.perf_counter()
    print(f"Data insertion completed in {end_time - start_time:.2f} seconds")

def get_counts():
    """
    Get counts of records in each table and print them.
    """
    device_count = clickhouse_client.execute( query="SELECT COUNT(*) FROM devices" )[0][0]
    sensor_count = clickhouse_client.execute( query="SELECT COUNT(*) FROM sensors" )[0][0]
    reading_count = clickhouse_client.execute( query="SELECT COUNT(*) FROM sensor_readings" )[0][0]
    alert_count = clickhouse_client.execute( query="SELECT COUNT(*) FROM alerts" )[0][0]

    print(f"Devices: {device_count}, Sensors: {sensor_count}, Readings: {reading_count}, Alerts: {alert_count}")

def execute_queries():
    """
    Execute analytical queries and print results.
    1. Average reading per device per day
    2. Max reading per sensor per device
    3. Average time between readings per sensor
    """
    print("Executing analytical queries...")

    avg_readings, time = timed(clickhouse_client.get_avg_reading_per_device_per_day)
    print(f"Average readings per device per day query executed in {time:.2f} seconds")

    max_readings, time = timed(clickhouse_client.get_sensor_extremes_per_device)
    print(f"Max readings query executed in {time:.2f} seconds")

    at, time = timed(clickhouse_client.get_avg_time_between_readings)
    print(f"Average time between readings query executed in {time:.2f} seconds")

insert()
get_counts()
execute_queries()
