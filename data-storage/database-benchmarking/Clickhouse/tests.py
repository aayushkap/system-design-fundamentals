import os
import uuid
import random
from datetime import datetime, timedelta
import csv
from faker import Faker

# ───── CONFIGURATION ─────
OUTPUT_DIR = "/data"
D = 10   # number of devices
S = 10    # sensors per device
R = 100000   # readings per sensor
A = 3    # alerts per device

fake = Faker()
now = datetime.utcnow()

# ensure output dir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ───── WRITE CSV HELPERS ─────
def write_csv(filename, header, rows):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")

# ───── GENERATE & DUMP ─────

# 1) devices.csv
device_rows = []
for i in range(1, D+1):
    dev_id = str(uuid.uuid4())
    name = f"dev{i}"
    loc  = fake.city()
    st   = random.choice(["online", "offline", "unknown"])
    device_rows.append([dev_id, name, loc, st])
write_csv("devices.csv",
          ["id", "name", "location", "status"],
          device_rows)

# 2) sensors.csv
sensor_rows = []
for dev_id, _, _, _ in device_rows:
    for j in range(1, S+1):
        sensor_id = str(uuid.uuid4())
        typ       = random.choice(["temp", "hum", "press"])
        sensor_rows.append([sensor_id, dev_id, typ])
write_csv("sensors.csv",
          ["id", "device_id", "type"],
          sensor_rows)

# 3) sensor_readings.csv
reading_rows = []
for sensor_id, dev_id, _ in sensor_rows:
    for k in range(1, R+1):
        # mix days up to 10 days back, plus a few random minutes
        ts = now - timedelta(
            days=random.randint(0, 10),
            minutes=k * random.random() * 5
        )
        val = round(random.random() * 100, 2)
        reading_id = str(uuid.uuid4())
        reading_rows.append([
            reading_id,
            sensor_id,
            ts.isoformat(),
            val
        ])
write_csv("sensor_readings.csv",
          ["id", "sensor_id", "reading_time", "reading_value"],
          reading_rows)

# 4) alerts.csv
alert_rows = []
for dev_id, _, _, _ in device_rows:
    for _ in range(A):
        ts     = now - timedelta(hours=random.random() * 24)
        atype  = random.choice(["overheat", "disconnect", "low-battery"])
        desc   = fake.sentence(nb_words=6)
        alert_id = str(uuid.uuid4())
        alert_rows.append([
            alert_id,
            dev_id,
            ts.isoformat(),
            atype,
            desc
        ])
write_csv("alerts.csv",
          ["id", "device_id", "alert_time", "alert_type", "description"],
          alert_rows)
