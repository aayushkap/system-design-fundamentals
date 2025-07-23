import time
from faker import Faker
from doris_client import DorisClient

from datetime import datetime, timedelta
import random
import uuid

fake = Faker()


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res = fn(*args, **kwargs)

    end = time.perf_counter()
    return res, (end - start)

print("Creating Doris client and schema...")
doris_client = DorisClient(batch_size=50000)
doris_client.create_schema()


# ── CONFIG ──
D = 10    # devices
S = 10    # sensors per device
R = 10000   # readings per sensor
A = 5    # alerts per device

now = datetime.utcnow()

# latency store

def insert():
    start_time = time.perf_counter()
    for i in range(1, D+1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc = fake.city()
        st = random.choice(["online", "offline", "unknown"])

        device_id = uuid.uuid4()
        _, t = timed(doris_client.insert_device,
                     str(device_id), name, loc, st)

        for j in range(1, S+1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp", "hum", "press"])
            sensor_id = uuid.uuid4()

            _, t = timed(doris_client.insert_sensor,
                         sensor_id, device_id, typ)

            for k in range(1, R+1):
                tstamp = now - timedelta(days=random.randint(0, 10),
                                         minutes=k * random.random() * 5)
                val = random.random() * 100
                reading_id = uuid.uuid4()

                _, t = timed(doris_client.bulk_insert_reading, reading_id, sensor_id, tstamp, val)


        for _ in range(A):
            tstamp = now - timedelta(hours=random.random()*24)
            atype = random.choice(["overheat", "disconnect", "low-battery"])
            desc = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            doris_client.insert_alert(
                alert_id, device_id, atype, tstamp, desc)

    doris_client.flush_readings()
    doris_client.conn.commit()

    end_time = time.perf_counter()
    print(f"Data insertion completed in {end_time - start_time:.2f} seconds")

def execute_queries():
    """
    Execute analytical queries and print results.
    1. Average reading per device per day
    2. Max reading per sensor per device
    3. Average time between readings per sensor
    """
    print("Executing analytical queries...")

    avg_readings, time = timed(doris_client.get_avg_reading_per_device_per_day)
    print(f"Average readings per device per day query executed in {time:.2f} seconds")

    max_readings, time = timed(doris_client.get_sensor_extremes_per_device)
    print(f"Max readings query executed in {time:.2f} seconds")

    at, time = timed(doris_client.get_avg_time_between_readings)
    print(f"Average time between readings query executed in {time:.2f} seconds")

insert()
# execute_queries()