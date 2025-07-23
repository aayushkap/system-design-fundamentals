import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime
from io import StringIO

class TimescaleClient:
    """
    A client for PostgreSQL with TimescaleDB extension enabled and hypertables.
    Optimized for maximum ingestion rates.
    """
    def __init__(self, db="iot", user="user", password="pass",
                 host="localhost", port=5433, batch_size=5000):
        self.conn = psycopg2.connect(
            dbname=db, user=user, password=password, host=host, port=port
        )
        self.cur = self.conn.cursor()
        psycopg2.extras.register_uuid(self.cur)

        # For buffered batch inserts
        self.batch_size = batch_size  # Reduced default to 10,000 for experimentation
        self._readings_buffer = []

    def create_schema(self):
        """
        Create the schema with optimized hypertable configuration.
        """
        # Enable extension
        self.cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

        # Create tables with composite PK on sensor_readings
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS devices(
          id UUID PRIMARY KEY,
          name TEXT,
          location TEXT,
          status TEXT
        );

        CREATE TABLE IF NOT EXISTS sensors(
          id UUID PRIMARY KEY,
          device_id UUID REFERENCES devices(id),
          type TEXT
        );

        CREATE TABLE IF NOT EXISTS sensor_readings(
          id UUID,
          sensor_id UUID NOT NULL REFERENCES sensors(id),
          reading_time TIMESTAMPTZ NOT NULL,
          reading_value DOUBLE PRECISION,
          PRIMARY KEY (reading_time, sensor_id, id)
        );

        CREATE TABLE IF NOT EXISTS alerts(
          id UUID PRIMARY KEY,
          device_id UUID REFERENCES devices(id),
          alert_type TEXT,
          alert_time TIMESTAMPTZ,
          description TEXT
        );
        """)

        # Convert to hypertable with space partitioning on sensor_id
        self.cur.execute(
            "SELECT create_hypertable('sensor_readings', 'reading_time', 'sensor_id', 10, if_not_exists => TRUE);"
        )
        self.cur.execute(
            "SELECT set_chunk_time_interval('sensor_readings', INTERVAL '15 minutes');"  # Smaller chunks for high ingestion
        )

        # Add index on sensor_id for query efficiency
        # self.cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_id ON sensor_readings(sensor_id);")

        # Set up retention and compression policies
        # self.cur.execute("SELECT add_drop_chunks_policy('sensor_readings', INTERVAL '30 days');")
        # self.cur.execute("SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');")

        self.conn.commit()

    def insert_device(self, id, name, location, status):
        self.cur.execute(
            "INSERT INTO devices(id, name, location, status) VALUES (%s, %s, %s, %s)",
            (id, name, location, status)
        )
        self.conn.commit()

    def insert_sensor(self, id, device_id, type_):
        self.cur.execute(
            "INSERT INTO sensors(id, device_id, type) VALUES (%s, %s, %s);",
            (id, device_id, type_)
        )
        self.conn.commit()

    def insert_reading(self, id, sensor_id, value, ts: datetime):
        self.cur.execute(
            "INSERT INTO sensor_readings(id, sensor_id, reading_time, reading_value) VALUES (%s, %s, %s, %s);",
            (id, sensor_id, ts, value)
        )
        self.conn.commit()

    def add_reading_to_batch(self, id, sensor_id, value, ts: datetime):
        """
        Buffer one reading and flush automatically when buffer is full.
        """
        self._readings_buffer.append((id, sensor_id, ts, value))
        if len(self._readings_buffer) >= self.batch_size:
            print(f"Flushing {len(self._readings_buffer)} readings to the database...")
            self.flush_readings()

    def flush_readings(self):
        """
        Flush buffered readings using COPY with optimized settings.
        """
        if not self._readings_buffer:
            return

        self.cur.execute("SET LOCAL synchronous_commit = OFF;")  # Disable synchronous commit for faster COPY

        # Build an in-memory CSV
        sio = StringIO()
        for _id, sensor_id, ts, val in self._readings_buffer:
            sio.write(f"{_id},{sensor_id},{ts.isoformat()},{val}\n")
        sio.seek(0)

        # Stream it into Postgres
        self.cur.copy_expert(
            """
            COPY sensor_readings (id, sensor_id, reading_time, reading_value)
            FROM STDIN WITH (FORMAT csv)
            """,
            sio
        )
        self.conn.commit()
        self._readings_buffer.clear()

    def insert_alert(self, id, device_id, atype, ts: datetime, desc):
        self.cur.execute(
            "INSERT INTO alerts(id, device_id, alert_type, alert_time, description) VALUES (%s, %s, %s, %s, %s);",
            (id, device_id, atype, ts, desc)
        )
        self.conn.commit()

    def get_all_tables(self):
        self.cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE';
        """
        )
        return [row[0] for row in self.cur.fetchall()]

    def execute_query(self, query, params=None):
        """Execute query with proper connection handling for large datasets."""
        try:
            if params:
                self.cur.execute(query, params)
            else:
                self.cur.execute(query)
            return self.cur.fetchall()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise e

    def average_reading_per_device_per_day(self):
        """
        Returns the average reading per device per day for the last 7 days, including device status.
        """
        query = """
        SELECT
          d.id AS device_id,
          d.name AS device_name,
          d.status,
          DATE(sr.reading_time) AS day,
          AVG(sr.reading_value) AS avg_reading
        FROM devices d
        JOIN sensors s ON s.device_id = d.id
        JOIN sensor_readings sr ON sr.sensor_id = s.id
        WHERE sr.reading_time >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY d.id, d.name, d.status, DATE(sr.reading_time)
        ORDER BY d.id, day;
        """
        return self.execute_query(query)

    def sensor_extremes_per_device(self):
        """
        Returns the sensors with max and min readings per device.
        """
        query = """
        SELECT
          d.id AS device_id,
          d.name AS device_name,
          s.id AS sensor_id,
          s.type AS sensor_type,
          sr.reading_value,
          sr.reading_time,
          'MAX' as extreme_type
        FROM devices d
        JOIN sensors s ON s.device_id = d.id
        JOIN sensor_readings sr ON sr.sensor_id = s.id
        JOIN (
          SELECT
            s2.device_id,
            MAX(sr2.reading_value) as max_value
          FROM sensors s2
          JOIN sensor_readings sr2 ON sr2.sensor_id = s2.id
          GROUP BY s2.device_id
        ) max_vals ON s.device_id = max_vals.device_id AND sr.reading_value = max_vals.max_value

        UNION ALL

        SELECT
          d.id AS device_id,
          d.name AS device_name,
          s.id AS sensor_id,
          s.type AS sensor_type,
          sr.reading_value,
          sr.reading_time,
          'MIN' as extreme_type
        FROM devices d
        JOIN sensors s ON s.device_id = d.id
        JOIN sensor_readings sr ON sr.sensor_id = s.id
        JOIN (
          SELECT
            s2.device_id,
            MIN(sr2.reading_value) as min_value
          FROM sensors s2
          JOIN sensor_readings sr2 ON sr2.sensor_id = s2.id
          GROUP BY s2.device_id
        ) min_vals ON s.device_id = min_vals.device_id AND sr.reading_value = min_vals.min_value

        ORDER BY device_id, reading_value DESC;
        """
        return self.execute_query(query)

    def average_time_between_readings_per_sensor(self):
        """
        Returns average time in seconds between consecutive readings per sensor.
        """
        query = """
        SELECT
          sr.sensor_id,
          AVG(time_diff) AS avg_seconds_between_readings
        FROM (
          SELECT
            sensor_id,
            EXTRACT(EPOCH FROM (reading_time - LAG(reading_time) OVER (ORDER BY reading_time))) AS time_diff
          FROM sensor_readings
          WHERE sensor_id IN (SELECT DISTINCT sensor_id FROM sensor_readings LIMIT 100)
        ) sr
        WHERE time_diff IS NOT NULL
        GROUP BY sr.sensor_id
        ORDER BY sr.sensor_id;
        """
        return self.execute_query(query)