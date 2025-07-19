import time
from faker import Faker
from timescale_client import TimescaleClient

from datetime import datetime, timedelta
import random
import uuid


fake = Faker()

def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res   = fn(*args, **kwargs)
    end   = time.perf_counter()
    return res, (end - start)

timescale_client = TimescaleClient()
timescale_client.create_schema()
print("TimescaleDB tables created:", timescale_client.get_all_tables())

# ── CONFIG ──
D = 10    # devices
S = 10    # sensors per device
R = 10000   # readings per sensor
A = 5    # alerts per device

now = datetime.utcnow()

avg_times = {}

query_times = {}

def insert():
    print("Beginning to insert data...")
    start = time.perf_counter()

    for i in range(1, D+1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc  = fake.city()
        st   = random.choice(["online","offline","unknown"])

        device_id = uuid.uuid4()
        _, t = timed(timescale_client.insert_device, device_id, name, loc, st)


        for j in range(1, S+1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp","hum","press"])
            sensor_id = uuid.uuid4()

            _, t = timed(timescale_client.insert_sensor, sensor_id, device_id, typ)


            for k in range(1, R+1):
                tstamp = now - timedelta(minutes=k * random.random() * 5)
                val    = random.random() * 100
                reading_id = uuid.uuid4()

                _, t = timed(timescale_client.add_reading_to_batch, reading_id, sensor_id, val, tstamp)


        for _ in range(A):
            tstamp = now - timedelta(hours=random.random()*24)
            atype  = random.choice(["overheat","disconnect","low-battery"])
            desc   = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            timescale_client.insert_alert(alert_id, device_id, atype, tstamp, desc)

    end = time.perf_counter()
    print(f"Total time for inserting data: {end - start:.2f} seconds\n")

insert()

print(timescale_client.execute_query(query = "SELECT COUNT(*) FROM sensor_readings;"))

# print("Query1: average_reading_per_device_per_day time: ", timed(timescale_client.average_reading_per_device_per_day))
# print("Query2: sensor_extremes_per_device time: ", timed(timescale_client.sensor_extremes_per_device))
# print("Query3: average_time_between_readings_per_sensor time: ", timed(timescale_client.average_time_between_readings_per_sensor))