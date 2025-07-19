import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

# CONFIGURATION
OUTPUT_DIR = "./data"
NUM_DEVICES  = 10     # Number of devices (configurable)
SENSORS_PER  = 10      # Number of sensors per device
READINGS_PER = 100000     # Number of readings per sensor
ALERTS_PER   = 3      # Number of alerts per device

fake = Faker()
now  = datetime.utcnow()

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_csv(df: pd.DataFrame, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} rows to {path}")

# 1) devices.csv
devices = []
for i in range(1, NUM_DEVICES + 1):
    dev_id = str(uuid.uuid4())
    devices.append({
        "id":       dev_id,
        "name":     f"dev{i}",
        "location": fake.city(),
        "status":   random.choice(["online", "offline", "unknown"])
    })
    df_devices = pd.DataFrame(devices)
    write_csv(df_devices, "devices")

    # 2) sensors.csv
    sensors = []
    for dev in devices:
        for j in range(1, SENSORS_PER + 1):
            sensors.append({
                "id":        str(uuid.uuid4()),
                "device_id": dev["id"],
                "type":      random.choice(["temp", "hum", "press"])
            })
        df_sensors = pd.DataFrame(sensors)
        write_csv(df_sensors, "sensors")

# 3) sensor_readings.csv
readings = []
for sensor in sensors:
    for _ in range(READINGS_PER):
        tstamp = now - timedelta(minutes=random.randint(0, 60*24))
        readings.append({
            "id":             str(uuid.uuid4()),
            "sensor_id":      sensor["id"],
            "reading_time":   tstamp.isoformat(),
            "reading_value":  round(random.random() * 100, 2)
        })
df_readings = pd.DataFrame(readings)
write_csv(df_readings, "sensor_readings")

# 4) alerts.csv
alerts = []
for dev in devices:
    for _ in range(ALERTS_PER):
        tstamp = now - timedelta(hours=random.random() * 24)
        alerts.append({
            "id":          str(uuid.uuid4()),
            "device_id":   dev["id"],
            "alert_time":  tstamp.isoformat(),
            "alert_type":  random.choice(["overheat", "disconnect", "low-battery"]),
            "description": fake.sentence(nb_words=6)
        })
df_alerts = pd.DataFrame(alerts)
write_csv(df_alerts, "alerts")
