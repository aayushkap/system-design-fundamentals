import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime

class TimescaleClient:
    """
    A client for PostgreSQL with TimescaleDB extension enabled and hypertables.
    """
    def __init__(self, db="iot", user="user", password="pass", host="localhost", port=5433):
        self.conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
        self.cur = self.conn.cursor()
        psycopg2.extras.register_uuid(self.cur)

    def create_schema(self):
        """
        Create the schema and convert sensor_readings to a hypertable.
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
          sensor_id UUID        NOT NULL REFERENCES sensors(id),
          reading_time TIMESTAMPTZ NOT NULL,
          reading_value DOUBLE PRECISION,
          PRIMARY KEY (id, reading_time)
        );

        CREATE TABLE IF NOT EXISTS alerts(
          id UUID PRIMARY KEY,
          device_id UUID REFERENCES devices(id),
          alert_type TEXT,
          alert_time TIMESTAMPTZ,
          description TEXT
        );
        """)

        # Convert to hypertable
        self.cur.execute(
            "SELECT create_hypertable('sensor_readings','reading_time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 hour');"
        )

        # In sensor_readings, we have 2 primary keys: sensor_id and reading_time.
        # This hypertable will partition the data by reading_time, which is suitable for time-series data.

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
        if params:
            self.cur.execute(query, params)
        else:
            self.cur.execute(query)
        return self.cur.fetchall()
