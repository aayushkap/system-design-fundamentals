import os
from cassandra.cluster import Cluster

class CassandraClient:
    def __init__(self, hosts=["127.0.0.1"]):
        self.cluster = Cluster(hosts)
        self.session = self.cluster.connect()

    def create_schema(self):
        # Create keyspace (database)
        self.session.execute("CREATE KEYSPACE IF NOT EXISTS iot WITH replication = {'class':'SimpleStrategy','replication_factor':'1'};")
        self.session.set_keyspace("iot")

        # Create tables
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS devices (
          id uuid PRIMARY KEY, name text, location text, status text
        );""")

        self.session.execute("""
        CREATE TABLE IF NOT EXISTS sensors (
          id uuid PRIMARY KEY, device_id uuid, type text
        );""")

        self.session.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
          id uuid, sensor_id uuid, reading_time timestamp, reading_value double,
          PRIMARY KEY(id, reading_time)
        ) WITH CLUSTERING ORDER BY (reading_time DESC);""")

        self.session.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
          id uuid, device_id uuid, alert_time timestamp, alert_type text, description text,
          PRIMARY KEY(id, alert_time)
        ) WITH CLUSTERING ORDER BY (alert_time DESC);""")

    def insert_device(self, id, name, location, status):
        self.session.execute(
            "INSERT INTO devices(id,name,location,status) VALUES(%s,%s,%s,%s)",
            (id,name,location,status))

    def insert_sensor(self, id, device_id, type):
        self.session.execute(
            "INSERT INTO sensors(id,device_id,type) VALUES(%s,%s,%s)",
            (id,device_id,type))

    def insert_reading(self, id, sensor_id, value, ts):
        self.session.execute(
            "INSERT INTO sensor_readings(id, sensor_id, reading_time, reading_value) VALUES(%s,%s,%s,%s)",
            (id, sensor_id, ts, value))

    def insert_alert(self, id, device_id, atype, ts, desc):
        self.session.execute(
            "INSERT INTO alerts(id, device_id, alert_time, alert_type, description) VALUES(%s,%s,%s,%s,%s)",
            (id, device_id, ts, atype, desc))

    def get_all_tables(self):
        return self.session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'iot';")

    def execute_query(self, query):
        # Cassandra
        return self.session.execute(query)