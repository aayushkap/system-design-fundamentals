import psycopg2
import psycopg2.extras
from datetime import datetime



class PostgresClient:
    """
    A client for standard PostgreSQL (no TimescaleDB extension).
    """
    def __init__(self, db="iot", user="user", password="pass", host="localhost", port=5432):
        self.conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
        self.cur = self.conn.cursor()
        psycopg2.extras.register_uuid(self.cur)

    def create_schema(self):
        """
        Create the schema for devices, sensors, readings, and alerts without TimescaleDB.
        """
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
          id UUID PRIMARY KEY,
          sensor_id UUID REFERENCES sensors(id),
          reading_value DOUBLE PRECISION,
          reading_time TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS alerts(
          id UUID PRIMARY KEY,
          device_id UUID REFERENCES devices(id),
          alert_type TEXT,
          alert_time TIMESTAMPTZ,
          description TEXT
        );
        """)
        self.conn.commit()

    def insert_device(self, id, name, location, status):
        self.cur.execute(
            "INSERT INTO devices(id, name, location, status) VALUES (%s, %s, %s, %s)",
            (id, name, location, status)
        )
        self.conn.commit()

    def insert_sensor(self, id, device_id, type_):
        self.cur.execute(
            "INSERT INTO sensors(id, device_id, type) VALUES (%s, %s, %s)",
            (id, device_id, type_)
        )
        self.conn.commit()

    def insert_reading(self, id, sensor_id, value, ts: datetime):
        self.cur.execute(
            "INSERT INTO sensor_readings(id, sensor_id, reading_value, reading_time) VALUES (%s, %s, %s, %s);",
            (id, sensor_id, value, ts)
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
        self.cur.execute(query, params)
        try:
            return self.cur.fetchall()
        except psycopg2.ProgrammingError:
            return None
