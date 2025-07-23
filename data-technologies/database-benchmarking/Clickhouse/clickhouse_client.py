import os
from clickhouse_driver import Client as CHClient
import pandas as pd

class ClickHouseClient:
    def __init__(self, host='localhost', batch_size=100):
        user = "myuser"
        password = "mypass"
        self.client = CHClient(
            host=host,
            user=user,
            password=password,
        )
        self.batch_size = batch_size
        self.readings_buffer = []  # Add buffer for batch inserts

    def create_schema(self):
        self.client.execute("CREATE DATABASE IF NOT EXISTS iot;")
        self.client.execute("USE iot;")

        # Device table
        self.client.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id UUID,
            name String,
            location String,
            status String
        ) ENGINE = MergeTree()
        ORDER BY (id);  # Better for point lookups
        """)

        # Sensor table
        self.client.execute("""
        CREATE TABLE IF NOT EXISTS sensors (
            id UUID,
            device_id UUID,
            type LowCardinality(String)  # Better for enum-like values
        ) ENGINE = MergeTree()
        ORDER BY (device_id, id);
        """)

        # Main readings table - Clickhouse is not natively optimized for aggregation, hence to optimize, we denormalize device_id
        self.client.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id UUID,
            sensor_id UUID,
            device_id UUID,  # Critical denormalization!
            reading_value Float64,
            reading_time DateTime
        ) ENGINE = MergeTree()
        ORDER BY (device_id, sensor_id, reading_time)  # Optimal for queries
        PARTITION BY toYYYYMM(reading_time)  # Monthly partitions
        TTL reading_time + INTERVAL 1 YEAR  # Auto-purging
        SETTINGS index_granularity = 8192;  # Default is fine
        """)

        # Materialized view for device metrics
        self.client.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS device_daily_metrics
        ENGINE = SummingMergeTree()
        ORDER BY (device_id, day)
        POPULATE AS
        SELECT
            device_id,
            toDate(reading_time) AS day,
            count() AS reading_count,
            sum(reading_value) AS value_sum
        FROM sensor_readings
        GROUP BY device_id, day;
        """)

        # Alerts table
        self.client.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID,
            device_id UUID,
            alert_type LowCardinality(String),
            alert_time DateTime,
            description String
        ) ENGINE = MergeTree()
        ORDER BY (device_id, alert_time);
        """)

    def insert_device(self, id, name, location, status):
        """Insert a device into the devices table"""
        self.client.execute(
            "INSERT INTO devices (id, name, location, status) VALUES",
            [(id, name, location, status)]
        )

    def insert_sensor(self, id, device_id, sensor_type):
        """Insert a sensor into the sensors table"""
        self.client.execute(
            "INSERT INTO sensors (id, device_id, type) VALUES",
            [(id, device_id, sensor_type)]
        )

    def insert_reading(self, id, sensor_id, device_id, value, ts):
        """Optimized batch insert with device_id denormalization"""

        self.readings_buffer.append((id, sensor_id, device_id, value, ts))

        if len(self.readings_buffer) >= self.batch_size:
            print(
                f"Flushing {len(self.readings_buffer)} readings to ClickHouse")
            self.flush_readings()

    def insert_alert(self, id, device_id, alert_type, ts, description):
        """Insert an alert into the alerts table"""
        self.client.execute(
            "INSERT INTO alerts (id, device_id, alert_type, alert_time, description) VALUES",
            [(id, device_id, alert_type, ts, description)]
        )

    def flush_readings(self):
        """Execute batch insert"""
        if not self.readings_buffer:
            return

        self.client.execute(
            "INSERT INTO sensor_readings (id, sensor_id, device_id, reading_value, reading_time) VALUES",
            self.readings_buffer
        )
        self.readings_buffer = []

    def force_flush(self):
        """Flush remaining records"""
        print("Forcing flush of remaining readings...: ",
              len(self.readings_buffer))
        self.flush_readings()

    def get_all_tables(self):
        """Get all tables in the ClickHouse database"""
        return self.client.execute("SHOW TABLES;")

    def execute(self, query, params=None):
        """Execute a query and return results"""
        if params:
            return self.client.execute(query, params)
        return self.client.execute(query)

    def clickhouse_to_df(self, query, params=None):
        """
        Execute a query on a clickhouse_driver Client and return a DataFrame.
        """
        if params:
            rows, cols = self.client.execute(query, params, with_column_types=True)
        else:
            rows, cols = self.client.execute(query, with_column_types=True)

        column_names = [col[0] for col in cols]

        return pd.DataFrame(rows, columns=column_names)

    # New analytical methods
    def get_avg_reading_per_device_per_day(self):
        query = """
        SELECT
            d.id AS device_id,
            d.name AS device_name,
            d.status,
            metrics.day,
            metrics.value_sum / metrics.reading_count AS avg_reading
        FROM devices d
        JOIN (
            SELECT
                device_id,
                day,
                sum(value_sum) AS value_sum,
                sum(reading_count) AS reading_count
            FROM device_daily_metrics
            WHERE day >= today() - 7
            GROUP BY device_id, day
        ) metrics ON d.id = metrics.device_id
        ORDER BY device_id, day
        """
        return self.clickhouse_to_df(query)

    def get_sensor_extremes_per_device(self):
        query = """
        SELECT
            ranked.device_id,
            ranked.device_name,
            ranked.sensor_id,
            ranked.sensor_type,
            ranked.reading_value,
            ranked.reading_time,
            IF(ranked.max_rank = 1, 'MAX', 'MIN') AS extreme_type
        FROM (
            SELECT
                sr.device_id               AS device_id,
                d.name                     AS device_name,
                sr.sensor_id               AS sensor_id,
                s.type                     AS sensor_type,
                sr.reading_value           AS reading_value,
                sr.reading_time            AS reading_time,
                RANK() OVER (
                  PARTITION BY sr.device_id
                  ORDER BY sr.reading_value DESC
                )                          AS max_rank,
                RANK() OVER (
                  PARTITION BY sr.device_id
                  ORDER BY sr.reading_value ASC
                )                          AS min_rank
            FROM sensor_readings AS sr
            INNER JOIN devices AS d
              ON d.id = sr.device_id
            INNER JOIN sensors AS s
              ON s.id = sr.sensor_id
        ) AS ranked
        WHERE ranked.max_rank = 1
           OR ranked.min_rank = 1
        ORDER BY ranked.device_id ASC, ranked.reading_value DESC
        """
        return self.clickhouse_to_df(query)

    def get_avg_time_between_readings(self):
        query = """
        WITH
            -- Step 1: compute “prev_time” per sensor
            lagged AS (
                SELECT
                    sensor_id,
                    reading_time,
                    lag(reading_time) OVER (
                        PARTITION BY sensor_id
                        ORDER BY reading_time
                    ) AS prev_time
                FROM sensor_readings
            ),
            -- Step 2: compute time_diff where prev_time exists
            diffs AS (
                SELECT
                    sensor_id,
                    reading_time - prev_time AS time_diff
                FROM lagged
                WHERE prev_time IS NOT NULL
            )
        -- Step 3: aggregate
        SELECT
            sensor_id,
            avg(time_diff) AS avg_seconds
        FROM diffs
        GROUP BY sensor_id
        """
        return self.clickhouse_to_df(query)
