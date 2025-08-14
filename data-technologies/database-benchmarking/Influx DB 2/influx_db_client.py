# influx_client.py
import time
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd


class InfluxDBClient2:
    def __init__(
        self,
        url="http://localhost:8086",
        token="test-token",
        org="test",
        readings_bucket="iot_readings",
        meta_bucket="iot_meta",
        alerts_bucket="iot_alerts",
        batch_size=1000,
    ):
        self.url = url
        self.token = token
        self.org = org
        self.readings_bucket = readings_bucket
        self.meta_bucket = meta_bucket
        self.alerts_bucket = alerts_bucket

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.buckets_api = self.client.buckets_api()

        # internal buffer for batch writes
        self.batch_size = batch_size
        self.readings_buffer = []

    # -----------------------
    # Buckets / schema
    # -----------------------
    def create_buckets(
        self,
        retention_days_readings=365,
        retention_days_meta=0,
        retention_days_alerts=90,
    ):
        """
        Create three buckets: meta_bucket, readings_bucket, alerts_bucket.
        retention_days = 0 => infinite retention
        """

        def ensure(name, retention_days):
            b = self.buckets_api.find_bucket_by_name(name)
            if b is None:
                retention_rules = None
                if retention_days and retention_days > 0:
                    retention_rules = [
                        {
                            "type": "expire",
                            "everySeconds": int(retention_days * 24 * 3600),
                        }
                    ]
                self.buckets_api.create_bucket(
                    bucket_name=name, org=self.org, retention_rules=retention_rules
                )
                print(f"Created bucket: {name}")

        ensure(self.readings_bucket, retention_days_readings)
        ensure(self.meta_bucket, retention_days_meta)
        ensure(self.alerts_bucket, retention_days_alerts)

    # -----------------------
    # Insert metadata
    # -----------------------
    def insert_device(self, id, name, location, status):
        """
        Write device metadata to meta_bucket measurement 'devices'.
        device_id and other identifiers are stored as tags for efficient joins and selection.
        """
        p = (
            Point("devices")
            .tag("device_id", str(id))
            .field("name", name)
            .field("status", status)
        )
        if location:
            p = p.field("location", location)
        self.write_api.write(bucket=self.meta_bucket, org=self.org, record=p)

    def insert_sensor(self, id, device_id, sensor_type):
        p = (
            Point("sensors")
            .tag("sensor_id", str(id))
            .tag("device_id", str(device_id))
            .field("type", sensor_type)
        )
        self.write_api.write(bucket=self.meta_bucket, org=self.org, record=p)

    # -----------------------
    # Readings (buffered)
    # -----------------------
    def insert_reading(self, id, sensor_id, device_id, value, ts=None):
        """
        Buffer readings as Points; flush when batch_size reached.
        - measurement: 'sensor_readings'
        - tags: sensor_id, device_id
        - field: value
        """
        if ts is None:
            ts = datetime.now(timezone.utc)
        elif isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)

        p = (
            Point("sensor_readings")
            .tag("sensor_id", str(sensor_id))
            .tag("device_id", str(device_id))
            .field("value", float(value))
            .time(ts, WritePrecision.NS)
        )

        self.readings_buffer.append(p)
        if len(self.readings_buffer) >= self.batch_size:
            self.flush_readings()

    def flush_readings(self):
        if not self.readings_buffer:
            return
        try:
            self.write_api.write(
                bucket=self.readings_bucket, org=self.org, record=self.readings_buffer
            )
            print(
                f"Flushed {len(self.readings_buffer)} readings to bucket {self.readings_bucket}"
            )
            self.readings_buffer = []
        except Exception as e:
            print("Error writing readings batch:", e)
            # keep buffer for retry

    def force_flush(self):
        print("Forcing flush of remaining readings:", len(self.readings_buffer))
        self.flush_readings()

    # -----------------------
    # Alerts
    # -----------------------
    def insert_alert(self, id, device_id, alert_type, ts=None, description=""):
        if ts is None:
            ts = datetime.now(timezone.utc)
        elif isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)

        p = (
            Point("alerts")
            .tag("device_id", str(device_id))
            .field("alert_type", alert_type)
            .field("description", description)
            .time(ts, WritePrecision.NS)
        )
        self.write_api.write(bucket=self.alerts_bucket, org=self.org, record=p)

    # -----------------------
    # Utilities & counts
    # -----------------------
    def get_all_buckets(self):
        buckets = self.buckets_api.find_buckets().buckets
        return [b.name for b in buckets]

    def get_counts(self):
        """
        Returns counts of records in devices / sensors / sensor_readings / alerts.
        Uses range(start: 1970-01-01) to count everything.
        """

        def count_measurement(bucket, measurement):
            flux = f"""
            from(bucket: "{bucket}")
            |> range(start: 1970-01-01T00:00:00Z)
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> count()
            |> distinct(column: "_value")
            |> keep(columns: ["_value"])
            """
            try:
                df = self.query_api.query_data_frame(flux, org=self.org)
                if isinstance(df, list):
                    df = df[0]
                if "_value" in df.columns and len(df) > 0:
                    return int(df["_value"].sum())
            except Exception as e:
                print("Count error:", e)
            return 0

        devices = count_measurement(self.meta_bucket, "devices")
        sensors = count_measurement(self.meta_bucket, "sensors")
        readings = count_measurement(self.readings_bucket, "sensor_readings")
        alerts = count_measurement(self.alerts_bucket, "alerts")
        return {
            "devices": devices,
            "sensors": sensors,
            "readings": readings,
            "alerts": alerts,
        }

    # -----------------------
    # Flux query helpers -> return pandas.DataFrame
    # -----------------------
    def execute_flux_to_df(self, flux_query: str):
        try:
            df = self.query_api.query_data_frame(flux_query, org=self.org)
            # query_data_frame may return list of DataFrames (tables)
            if isinstance(df, list):
                df = pd.concat(df, ignore_index=True)
            # drop system columns often present
            for c in ["result", "table"]:
                if c in df.columns:
                    df = df.drop(columns=c)
            return df
        except Exception as e:
            print("Flux query error:", e)
            return pd.DataFrame()

    # -----------------------
    # Analytical queries (Flux) — DB does the work
    # -----------------------
    def get_avg_reading_per_device_per_day(self, days=7):
        flux = f"""
        readings_daily = from(bucket: "{self.readings_bucket}")
        |> range(start: -{days}d)
        |> filter(fn: (r) => r._measurement == "sensor_readings" and r._field == "value")
        |> group(columns: ["device_id"])
        |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
        |> keep(columns: ["_time", "device_id", "_value"])
        |> rename(columns: {{_time: "day", _value: "avg_reading"}})

        devices = from(bucket: "{self.meta_bucket}")
        |> range(start: 1970-01-01T00:00:00Z)
        |> filter(fn: (r) => r._measurement == "devices")
        |> last()
        |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn: "_value")
        |> keep(columns: ["device_id", "name", "status"])

        join(tables: {{r: readings_daily, d: devices}}, on: ["device_id"])
        |> keep(columns: ["device_id", "name", "status", "day", "avg_reading"])
        |> rename(columns: {{name: "device_name"}})
        |> sort(columns: ["device_id", "day"])
        """
        return self.execute_flux_to_df(flux)


    def get_sensor_extremes_per_device(self, days=30):
        flux = f"""
    readings = from(bucket: "{self.readings_bucket}")
    |> range(start: -{days}d)
    |> filter(fn: (r) => r._measurement == "sensor_readings" and r._field == "value")
    |> keep(columns: ["_time", "sensor_id", "device_id", "_value"])

    max_per_device = readings
    |> group(columns: ["device_id"])
    |> top(n: 1, columns: ["_value"])
    |> rename(columns: {{_time: "reading_time", _value: "reading_value"}})
    |> keep(columns: ["device_id", "sensor_id", "reading_value", "reading_time"])

    min_per_device = readings
    |> group(columns: ["device_id"])
    |> bottom(n: 1, columns: ["_value"])
    |> rename(columns: {{_time: "reading_time", _value: "reading_value"}})
    |> keep(columns: ["device_id", "sensor_id", "reading_value", "reading_time"])

    sensors = from(bucket: "{self.meta_bucket}")
    |> range(start: 1970-01-01T00:00:00Z)
    |> filter(fn: (r) => r._measurement == "sensors")
    |> last()
    |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn: "_value")
    |> keep(columns: ["sensor_id", "device_id", "type"])

    devices = from(bucket: "{self.meta_bucket}")
    |> range(start: 1970-01-01T00:00:00Z)
    |> filter(fn: (r) => r._measurement == "devices")
    |> last()
    |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn: "_value")
    |> keep(columns: ["device_id", "name"])

    max_join = join(tables: {{r: max_per_device, s: sensors}}, on: ["sensor_id"])
    max_join_final = join(tables: {{m: max_join, d: devices}}, on: ["device_id"])
    |> set(key: "extreme", value: "MAX")
    |> keep(columns: ["device_id", "name", "sensor_id", "type", "reading_value", "reading_time", "extreme"])
    |> rename(columns: {{name: "device_name", type: "sensor_type"}})

    min_join = join(tables: {{r: min_per_device, s: sensors}}, on: ["sensor_id"])
    min_join_final = join(tables: {{m: min_join, d: devices}}, on: ["device_id"])
    |> set(key: "extreme", value: "MIN")
    |> keep(columns: ["device_id", "name", "sensor_id", "type", "reading_value", "reading_time", "extreme"])
    |> rename(columns: {{name: "device_name", type: "sensor_type"}})

    union(tables: [max_join_final, min_join_final])
    |> sort(columns: ["device_id", "reading_value"], desc: true)
    """
        return self.execute_flux_to_df(flux)




    def get_avg_time_between_readings(self, days=30):
        """
        Average time between readings per sensor (seconds) — uses elapsed() on grouped sensor_id.
        """
        flux = f"""
            from(bucket: "{self.readings_bucket}")
            |> range(start: -{days}d)
            |> filter(fn: (r) => r._measurement == "sensor_readings" and r._field == "value")
            |> sort(columns: ["_time"])
            |> group(columns: ["sensor_id"])
            |> elapsed(unit: 1s)
            |> mean(column: "_value")
            |> rename(columns: {{_value: "avg_seconds_between_readings"}})
            |> keep(columns: ["sensor_id", "avg_seconds_between_readings"])
            """
        return self.execute_flux_to_df(flux)
