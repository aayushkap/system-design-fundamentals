import os
from clickhouse_driver import Client as CHClient

class ClickHouseClient:
    def __init__(self, host='localhost'):
        user = "myuser"
        password = "mypass"
        self.client = CHClient(
            host=host,
            user=user,
            password=password,
        )

    def create_schema(self):

        self.client.execute("CREATE DATABASE IF NOT EXISTS iot;")
        self.client.execute("USE iot;")

        self.client.execute("""
          CREATE TABLE IF NOT EXISTS devices (
            id UUID,
            name String, location String, status String
          ) ENGINE = MergeTree() ORDER BY id;
        """)

        self.client.execute("""
          CREATE TABLE IF NOT EXISTS sensors (
            id UUID, device_id UUID, type String
          ) ENGINE = MergeTree() ORDER BY id;
        """)

        self.client.execute("""
          CREATE TABLE IF NOT EXISTS sensor_readings (
            id UUID, sensor_id UUID, reading_value Float64, reading_time DateTime
          ) ENGINE = MergeTree() ORDER BY (sensor_id, reading_time);
        """)

        self.client.execute("""
          CREATE TABLE IF NOT EXISTS alerts (
            id UUID, device_id UUID, alert_type String, alert_time DateTime, description String
          ) ENGINE = MergeTree() ORDER BY (device_id, alert_time);
        """)

    def insert_device(self, id, name, location, status):
        self.client.execute(
            "INSERT INTO devices VALUES",( [(id, name, location, status)] )
        )

    def insert_sensor(self, id, device_id, type):
        self.client.execute("INSERT INTO sensors VALUES", [(id, device_id, type)])

    def insert_reading(self, id, sensor_id, value, ts):
        self.client.execute("INSERT INTO sensor_readings VALUES", [(id, sensor_id, value, ts)])

    def insert_alert(self, id, device_id, atype, ts, desc):
        self.client.execute("INSERT INTO alerts VALUES", [(id, device_id, atype, ts, desc)])

    def get_all_tables(self):
        return self.client.execute("SHOW TABLES FROM iot;")

    def execute_query(self, query):
        # ClickHouse
        return self.client.execute(query)