import time
from faker import Faker
from clients.cassandra_client import CassandraClient
from clients.postgres_client import PostgresClient
from clients.timescale_client import TimescaleClient
from clients.clickhouse_client import ClickHouseClient
from clients.mongo_client import MongoDBClient

from datetime import datetime, timedelta
import random
import uuid
import statistics

from plot_results import main as plot_main

fake = Faker()

def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    res   = fn(*args, **kwargs)
    end   = time.perf_counter()
    return res, (end - start)

# Instantiate clients. Wait ~30s for Cassandra to be ready.
cassandra_client = CassandraClient()
cassandra_client.create_schema()
print("Cassandra keyspace and tables created:", cassandra_client.get_all_tables())

clickhouse_client = ClickHouseClient()
clickhouse_client.create_schema()
print("ClickHouse database and tables created:", clickhouse_client.get_all_tables())

postgres_client = PostgresClient()
postgres_client.create_schema()
print("Postgres tables created:", postgres_client.get_all_tables())

timescale_client = TimescaleClient()
timescale_client.create_schema()
print("TimescaleDB tables created:", timescale_client.get_all_tables())

mongo_client = MongoDBClient()
mongo_client.create_schema()
print("MongoDB collections created:", mongo_client.get_all_tables())


# ── CONFIG ──
D = 1    # devices
S = 5    # sensors per device
R = 10   # readings per sensor
A = 5    # alerts per device

now = datetime.utcnow()

# latency store
times = {
    "cas_dev": [], "ch_dev": [], "pg_dev": [], "ts_dev": [], "mg_dev": [],
    "cas_sen": [], "ch_sen": [], "pg_sen": [], "ts_sen": [], "mg_sen": [],
    "cas_read":[], "ch_read":[], "pg_read":[], "ts_read":[], "mg_read":[],
}

avg_times = {}

query_times = {}

def insert():
    print("Beginning to insert data...")

    for i in range(1, D+1):
        print(f"-> Device {i}/{D}")
        name = f"dev{i}"
        loc  = fake.city()
        st   = random.choice(["online","offline","unknown"])

        device_id = uuid.uuid4()
        _, t = timed(cassandra_client.insert_device, device_id, name, loc, st)
        times["cas_dev"].append(t)
        _, t = timed(clickhouse_client.insert_device, str(device_id), name, loc, st)
        times["ch_dev"].append(t)
        _, t = timed(postgres_client.insert_device, device_id, name, loc, st)
        times["pg_dev"].append(t)
        _, t = timed(timescale_client.insert_device, device_id, name, loc, st)
        times["ts_dev"].append(t)
        _, t = timed(mongo_client.insert_device, device_id, name, loc, st)
        times["mg_dev"].append(t)

        for j in range(1, S+1):
            print(f"\t-> Sensor {j}/{S}")
            typ = random.choice(["temp","hum","press"])
            sensor_id = uuid.uuid4()

            _, t = timed(cassandra_client.insert_sensor, sensor_id, device_id, typ)
            times["cas_sen"].append(t)
            _, t = timed(clickhouse_client.insert_sensor, sensor_id, device_id, typ)
            times["ch_sen"].append(t)
            _, t = timed(postgres_client.insert_sensor, sensor_id, device_id, typ)
            times["pg_sen"].append(t)
            _, t = timed(timescale_client.insert_sensor, sensor_id, device_id, typ)
            times["ts_sen"].append(t)
            _, t = timed(mongo_client.insert_sensor, sensor_id, device_id, typ)
            times["mg_sen"].append(t)

            for k in range(1, R+1):
                tstamp = now - timedelta(minutes=k * random.random() * 5)
                val    = random.random() * 100
                reading_id = uuid.uuid4()

                _, t = timed(cassandra_client.insert_reading, reading_id, sensor_id, val, tstamp)
                times["cas_read"].append(t)
                _, t = timed(clickhouse_client.insert_reading, reading_id, sensor_id, val, tstamp)
                times["ch_read"].append(t)
                _, t = timed(postgres_client.insert_reading, reading_id, sensor_id, val, tstamp)
                times["pg_read"].append(t)
                _, t = timed(timescale_client.insert_reading, reading_id, sensor_id, val, tstamp)
                times["ts_read"].append(t)
                _, t = timed(mongo_client.insert_reading, reading_id, sensor_id, val, tstamp)
                times["mg_read"].append(t)

        for _ in range(A):
            tstamp = now - timedelta(hours=random.random()*24)
            atype  = random.choice(["overheat","disconnect","low-battery"])
            desc   = fake.sentence(nb_words=6)
            alert_id = uuid.uuid4()
            cassandra_client.insert_alert(alert_id, device_id, atype, tstamp, desc)
            clickhouse_client.insert_alert(alert_id, device_id, atype, tstamp, desc)
            postgres_client.insert_alert(alert_id, device_id, atype, tstamp, desc)
            timescale_client.insert_alert(alert_id, device_id, atype, tstamp, desc)
            mongo_client.insert_alert(alert_id, device_id, atype, tstamp, desc)

    print("Data insertion completed.\n")


    # Summary of averages
    print("Average insert times (ms):")
    for k, lst in times.items():
        if not lst:
            continue
        avg_ms = statistics.mean(lst) * 1000
        print(f"  {k:8s}: {avg_ms:7.2f} ms")

    avg_times = {}
    print("Average insert times (ms):")
    for k, lst in times.items():
        if not lst:
            continue
        avg_ms = statistics.mean(lst) * 1000
        avg_times[k] = avg_ms
        print(f"  {k:8s}: {avg_ms:7.2f} ms")

    return avg_times

def read():
    # SQL for SQL‑engines
    count_sql = "SELECT COUNT(*) FROM sensor_readings;"

    # Postgres
    _, t = timed(postgres_client.execute_query, count_sql)
    print(f"Postgres COUNT(*) → {t*1000:7.2f} ms, : ", _)

    query_times["pg_query_1"] = t

    # TimescaleDB (identical syntax)
    _, t = timed(timescale_client.execute_query, count_sql)
    print(f"TimescaleDB COUNT(*) → {t*1000:7.2f} ms, : ", _)

    query_times["ts_query_1"] = t

    # ClickHouse (same SQL, just lowercase interval if needed)
    _, t = timed(clickhouse_client.execute_query, count_sql)
    print(f"ClickHouse COUNT(*) → {t*1000:7.2f} ms, : ", _)

    query_times["ch_query_1"] = t

    # MongoDB
    def mongo_count():
        # uses the count_documents() driver method for the collection
        return mongo_client.db.sensor_readings.count_documents({})

    _, t = timed(mongo_count)
    print(f"MongoDB count_documents → {t*1000:7.2f} ms: ", _)

    query_times["mg_query_1"] = t

    # Cassandra
    # Note: Cassandra COUNT(*) without a partition key will do a full scan.
    def cass_count():
        row = cassandra_client.execute_query("SELECT COUNT(*) FROM sensor_readings;")
        return row[0][0]

    _, t = timed(cass_count)
    print(f"Cassandra COUNT(*) → {t*1000:7.2f} ms: ", _)

    query_times["cas_query_1"] = t

def complex_query():
    print("\n\nRunning complex query: average sensor readings for each device in the last 3 hours...")
    # 1h ago
    cutoff = datetime.utcnow() - timedelta(hours=3)

    # SQL for SQL‑engines
    sql = """
      SELECT d.name,
             AVG(r.reading_value) AS avg_val
        FROM devices d
        JOIN sensors s ON s.device_id=d.id
        JOIN sensor_readings r ON r.sensor_id=s.id
       WHERE r.reading_time > NOW() - INTERVAL '3 hour'
       GROUP BY d.name
       ORDER BY d.name;
    """

    # Postgres
    res, t = timed(postgres_client.execute_query, sql)
    print(f"Postgres → {t*1000:7.2f} ms: {res}")

    query_times["pg_query_2"] = t

    # TimescaleDB
    res, t = timed(timescale_client.execute_query, sql)
    print(f"TimescaleDB → {t*1000:7.2f} ms: {res}")

    query_times["ts_query_2"] = t

    # ClickHouse (adjust NOW syntax)
    ch_sql = sql.replace("NOW() - INTERVAL '3 hour'", "now() - INTERVAL 3 HOUR")
    res, t = timed(clickhouse_client.execute_query, ch_sql)
    print(f"ClickHouse → {t*1000:7.2f} ms: {res}")

    query_times["ch_query_2"] = t

    # MongoDB aggregation pipeline
    res, t = timed(
        lambda: list(
            mongo_client.db.sensor_readings.aggregate([
                {"$match": {"reading_time": {"$gt": cutoff}}},
                {"$lookup": {
                    "from": "sensors",
                    "localField": "sensor_id",
                    "foreignField": "_id",
                    "as": "s"
                }},
                {"$unwind": "$s"},
                {"$lookup": {
                    "from": "devices",
                    "localField": "s.device_id",
                    "foreignField": "_id",
                    "as": "d"
                }},
                {"$unwind": "$d"},
                {"$group": {
                    "_id": "$d.name",
                    "avgVal": {"$avg": "$reading_value"}
                }},
                {"$sort": {"_id": 1}}
            ])
        )
    )
    print(f"MongoDB → {t*1000:7.2f} ms: {res}")

    query_times["mg_query_2"] = t

    # Cassandra: client‑side aggregation
    def cass_avg():
        # get readings and sensor→device map
        rows = cassandra_client.execute_query(
            "SELECT sensor_id, reading_value, reading_time FROM sensor_readings;"
        )
        sens = cassandra_client.execute_query("SELECT id, device_id FROM sensors;")
        devs = cassandra_client.execute_query("SELECT id, name FROM devices;")
        # build maps
        sensor_map = {sid: did for sid, did in sens}
        device_name = {did: name for did, name in devs}
        agg = {}
        for sid, val, ts in rows:
            if ts < cutoff:
                continue
            did = sensor_map[sid]
            name = device_name[did]
            agg.setdefault(name, []).append(val)
        return {name: sum(vals)/len(vals) for name, vals in agg.items()}

    res, t = timed(cass_avg)
    print(f"Cassandra → {t*1000:7.2f} ms: {res}")

    query_times["cas_query_2"] = t

avg_times = insert()
read()
complex_query()

print("\n\nQuery times:")
for k, v in query_times.items():
    print(f"{k:10s}: {v*1000:7.2f} ms")

plot_main(times, query_times)