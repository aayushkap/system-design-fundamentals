import pymysql
import pandas as pd


class DorisClient:
    def __init__(self, host='localhost', user='admin', password='', port=9030, batch_size=10000):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            autocommit=False
        )
        self.cursor = self.conn.cursor()

        self.batch_size = batch_size
        self.reading_buffer = []  # buffer for batched reading inserts

    def create_schema(self):
        # Create database
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS iot;")
        self.cursor.execute("USE iot;")

        # Create tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id VARCHAR(36),
                name VARCHAR(255),
                location VARCHAR(255),
                status VARCHAR(50)
            ) ENGINE=OLAP
            DUPLICATE KEY(id)
            DISTRIBUTED BY HASH(id) BUCKETS 3
            PROPERTIES ("replication_num" = "1");
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id VARCHAR(36),
                device_id VARCHAR(36),
                type VARCHAR(100)
            ) ENGINE=OLAP
            DUPLICATE KEY(id)
            DISTRIBUTED BY HASH(id) BUCKETS 3
            PROPERTIES ("replication_num" = "1");
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id VARCHAR(36),
                sensor_id VARCHAR(36),
                reading_time DATETIME,
                reading_value DOUBLE
            ) ENGINE=OLAP
            DUPLICATE KEY(id)
            DISTRIBUTED BY HASH(id) BUCKETS 6
            PROPERTIES ("replication_num" = "1");
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id VARCHAR(36),
                device_id VARCHAR(36),
                alert_time DATETIME,
                alert_type VARCHAR(100),
                description TEXT
            ) ENGINE=OLAP
            DUPLICATE KEY(id)
            DISTRIBUTED BY HASH(id) BUCKETS 3
            PROPERTIES ("replication_num" = "1");
        """)

    def insert_device(self, id, name, location, status):
        sql = "INSERT INTO devices (id, name, location, status) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(sql, (id, name, location, status))

    def insert_sensor(self, id, device_id, sensor_type):
        sql = "INSERT INTO sensors (id, device_id, type) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (id, device_id, sensor_type))

    def bulk_insert_reading(self, id, sensor_id, reading_time, reading_value):
        self.reading_buffer.append(
            (id, sensor_id, reading_time, reading_value))

        if len(self.reading_buffer) >= self.batch_size:
            self.flush_readings()

    def flush_readings(self):
        if not self.reading_buffer:
            return

        sql = "INSERT INTO sensor_readings (id, sensor_id, reading_time, reading_value) VALUES (%s, %s, %s, %s)"
        self.cursor.executemany(sql, self.reading_buffer)
        self.conn.commit()  # Commit the batch insert

        # Clear buffer after flush
        self.reading_buffer.clear()

    def insert_alert(self, id, device_id, alert_time, alert_type, description):
        sql = "INSERT INTO alerts (id, device_id, alert_time, alert_type, description) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(
            sql, (id, device_id, alert_time, alert_type, description))

    def execute(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()

    # Example analytical query methods:
    def get_avg_reading_per_device_per_day(self):
        query = """
        SELECT
            s.device_id,
            DATE(r.reading_time) AS day,
            AVG(r.reading_value) AS avg_value
        FROM sensor_readings r
        JOIN sensors s ON r.sensor_id = s.id
        GROUP BY s.device_id, day
        ORDER BY s.device_id, day;
        """
        return self.execute(query)

    def get_sensor_extremes_per_device(self):
        query = """
        SELECT
            s.device_id,
            s.id AS sensor_id,
            MAX(r.reading_value) AS max_value,
            MIN(r.reading_value) AS min_value
        FROM sensor_readings r
        JOIN sensors s ON r.sensor_id = s.id
        GROUP BY s.device_id, s.id
        ORDER BY s.device_id, s.id;
        """
        return self.execute(query)

    def get_avg_time_between_readings(self):
        query = """
        SELECT
            sensor_id,
            AVG(diff_seconds) AS avg_seconds
        FROM (
            SELECT
                sensor_id,
                TIMESTAMPDIFF(SECOND,
                    LAG(reading_time) OVER (PARTITION BY sensor_id ORDER BY reading_time),
                    reading_time
                ) AS diff_seconds
            FROM sensor_readings
        ) t
        WHERE diff_seconds IS NOT NULL
        GROUP BY sensor_id;
        """
        return self.execute(query)
