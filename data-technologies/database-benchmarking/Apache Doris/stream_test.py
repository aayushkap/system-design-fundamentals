import io
import csv
import uuid
import requests
import time
from faker import Faker
from doris_client import DorisClient

from datetime import datetime, timedelta
import random
import uuid
import requests
from requests.auth import HTTPBasicAuth

def stream_load_readings_to_doris(rows,
								  fe_host="localhost",
								  fe_http_port=8030,
								  database="iot",
								  user="admin",
								  password="",
								  table="sensor_readings"):

	# 1) Build CSV in memory
	buf = io.StringIO()
	writer = csv.writer(buf)

	for (rid, sensor_id, ts, val) in rows:
		# ensure timestamp is ISO-formatted string
		ts_str = ts.isoformat(sep=' ')
		writer.writerow([rid, sensor_id, ts_str, val])

	payload = buf.getvalue().encode("utf-8")
	buf.close()

	url = f"http://{fe_host}:{fe_http_port}/api/{database}/{table}/_stream_load"

	headers = {
		"label":               "stream_load_" + uuid.uuid4().hex,
		"format":              "CSV",
		"strip_outer_array":   "true",
			"Expect": "100-continue",  

	}
	
	auth = HTTPBasicAuth(user, password)    

	# 4) Send
	print(f"Sending stream load to {url} with {len(rows)} rows")
	resp = requests.put(url, data=payload, headers=headers, auth=auth)
	resp.raise_for_status()
	result = resp.json()
	if result.get("Status", "").lower() != "success":
		raise RuntimeError(f"Stream load failed: {result}")
	return result

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


my_buffer = []
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

				my_buffer.append((reading_id, sensor_id, tstamp, val))

				if len(my_buffer) >= doris_client.batch_size:
					stream_load_readings_to_doris(my_buffer)
					my_buffer.clear()

	# final flush
	if my_buffer:
		stream_load_readings_to_doris(my_buffer)
		
insert()