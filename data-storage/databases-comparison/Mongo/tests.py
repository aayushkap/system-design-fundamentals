import time
from faker import Faker
from mongo_client import MongoDBClient

from datetime import datetime, timedelta
import random
import uuid

fake = Faker()

def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res   = fn(*args, **kwargs)
    end   = time.perf_counter()
    return res, (end - start)


mongo_client = MongoDBClient()
mongo_client.create_schema()
print("MongoDB collections created:", mongo_client.get_all_tables())

# ── CONFIG ──
D = 10    # devices
S = 10    # sensors per device
R = 100000   # readings per sensor
A = 5    # alerts per device

now = datetime.utcnow()

BATCH_SIZE = 100

def flush_and_clear(buffer, flush_fn):
    if buffer:
        flush_fn(buffer)
        buffer.clear()

def insert():
    print("Beginning to insert data...")
    start = time.perf_counter()

    device_docs = []
    sensor_docs = []
    reading_docs = []
    alert_docs = []

    for i in range(1, D + 1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc = fake.city()
        st = random.choice(["online", "offline", "unknown"])

        device_id = uuid.uuid4()
        device_docs.append({
            "id": device_id,
            "name": name,
            "location": loc,
            "status": st
        })
        if len(device_docs) >= BATCH_SIZE:
            mongo_client.insert_device_bulk(device_docs)
            device_docs.clear()

        for j in range(1, S + 1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp", "hum", "press"])
            sensor_id = uuid.uuid4()

            sensor_docs.append({
                "id": sensor_id,
                "device_id": device_id,
                "type": typ
            })
            if len(sensor_docs) >= BATCH_SIZE:
                mongo_client.insert_sensor_bulk(sensor_docs)
                sensor_docs.clear()

            for k in range(1, R + 1):
                tstamp = now - timedelta(days=random.randint(0, 15),
                                         minutes=k * random.random() * 5)
                val = random.random() * 100
                reading_id = uuid.uuid4()
                reading_docs.append({
                    "id": reading_id,
                    "sensor_id": sensor_id,
                    "reading_value": val,
                    "reading_time": tstamp
                })
                if len(reading_docs) >= BATCH_SIZE:
                    mongo_client.insert_reading_bulk(reading_docs)
                    reading_docs.clear()

        for _ in range(A):
            tstamp = now - timedelta(hours=random.random() * 24)
            atype = random.choice(["overheat", "disconnect", "low-battery"])
            desc = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            alert_docs.append({
                "id": alert_id,
                "device_id": device_id,
                "alert_type": atype,
                "alert_time": tstamp,
                "description": desc
            })
            if len(alert_docs) >= BATCH_SIZE:
                mongo_client.insert_alert_bulk(alert_docs)
                alert_docs.clear()

    # flush
    flush_and_clear(device_docs, mongo_client.insert_device_bulk)
    flush_and_clear(sensor_docs, mongo_client.insert_sensor_bulk)
    flush_and_clear(reading_docs, mongo_client.insert_reading_bulk)
    flush_and_clear(alert_docs, mongo_client.insert_alert_bulk)

    end = time.perf_counter()
    print(f"Data insertion completed in {end - start:.2f} seconds.")

def get_counts():
    counts = {
        "devices": mongo_client.db.devices.count_documents({}),
        "sensors": mongo_client.db.sensors.count_documents({}),
        "sensor_readings": mongo_client.db.sensor_readings.count_documents({}),
        "alerts": mongo_client.db.alerts.count_documents({})
    }
    for collection, count in counts.items():
        print(f"{collection}: {count} documents")
    return counts

def execute_queries():
    """
    Execute analytical queries and print results.
    1. Average reading per device per day
    2. Max reading per sensor per device
    3. Average time between readings per sensor
    """
    print("Executing analytical queries...")

    # avg_readings, time = timed(mongo_client.get_avg_reading_per_device_per_day)
    # print(f"Average readings per device per day query executed in {time:.2f} seconds")

    # print("Average readings per device per day:")
    # for device in avg_readings:
    #     print(device)

    max_readings, time = timed(mongo_client.get_sensor_extremes_per_device)
    print(f"Max readings query executed in {time:.2f} seconds")
    print("Max readings per sensor per device:")
    for device in max_readings:
        print(device)

    # at, time = timed(mongo_client.get_avg_time_between_readings)
    # print(f"Average time between readings query executed in {time:.2f} seconds")
    # print("Average time between readings per sensor:")
    # for sensor in at:
    #     print(sensor)


# insert()
get_counts()
execute_queries()