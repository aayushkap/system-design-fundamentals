import os
from pymongo import MongoClient, InsertOne
from faker import Faker
from datetime import datetime, timedelta

class MongoDBClient:
    def __init__(self, uri="mongodb://localhost:27017/", db="iot"):
        self.client = MongoClient(uri, uuidRepresentation="standard")
        self.db = self.client[db]

    def create_schema(self):
        # Mongo is schemaless; ensure indexes
        self.db.devices.create_index("id", unique=True)
        self.db.sensors.create_index("id", unique=True)
        self.db.sensor_readings.create_index([("sensor_id", 1), ("reading_time", 1)])
        self.db.alerts.create_index("device_id")

    def insert_device(self, id, name, location, status):
        return self.db.devices.insert_one({
            "id": id,
            "name": name,
            "location": location,
            "status": status
        })

    def insert_sensor(self, id, device_id, type_):
        return self.db.sensors.insert_one({
            "id": id,
            "device_id": device_id,
            "type": type_
        }).inserted_id

    def insert_reading(self, id, sensor_id, value, ts):
        return self.db.sensor_readings.insert_one({
            "id": id,
            "sensor_id": sensor_id,
            "reading_value": value,
            "reading_time": ts
        })

    def insert_alert(self, id, device_id, atype, ts, desc):
        return self.db.alerts.insert_one({
            "id": id,
            "device_id": device_id,
            "alert_type": atype,
            "alert_time": ts,
            "description": desc
        })

    def insert_device_bulk(self, devices):
        """
        devices: list of dicts with keys id, name, location, status
        """
        if not devices:
            return None
        ops = [InsertOne({
            "id": d["id"],
            "name": d["name"],
            "location": d["location"],
            "status": d["status"]
        }) for d in devices]
        return self.db.devices.bulk_write(ops, ordered=False)

    def insert_sensor_bulk(self, sensors):
        """
        sensors: list of dicts with keys id, device_id, type
        """
        if not sensors:
            return None
        ops = [InsertOne({
            "id": s["id"],
            "device_id": s["device_id"],
            "type": s["type"]
        }) for s in sensors]
        return self.db.sensors.bulk_write(ops, ordered=False)

    def insert_reading_bulk(self, readings):
        """
        readings: list of dicts with keys id, sensor_id, reading_value, reading_time
        """
        if not readings:
            return None
        ops = [InsertOne({
            "id": r["id"],
            "sensor_id": r["sensor_id"],
            "reading_value": r["reading_value"],
            "reading_time": r["reading_time"]
        }) for r in readings]
        return self.db.sensor_readings.bulk_write(ops, ordered=False)

    def insert_alert_bulk(self, alerts):
        """
        alerts: list of dicts with keys id, device_id, alert_type, alert_time, description
        """
        if not alerts:
            return None
        ops = [InsertOne({
            "id": a["id"],
            "device_id": a["device_id"],
            "alert_type": a["alert_type"],
            "alert_time": a["alert_time"],
            "description": a["description"]
        }) for a in alerts]
        return self.db.alerts.bulk_write(ops, ordered=False)

    def get_all_tables(self):
        return self.db.list_collection_names()

    def execute_query(self, query):
        # MongoDB queries are typically done through the collection interface
        collection_name = query.get("collection")
        if not collection_name:
            raise ValueError("Query must specify a collection")
        collection = self.db[collection_name]
        return list(collection.find(query.get("filter", {}), query.get("projection", None)))

    def get_avg_reading_per_device_per_day(self):
        """Average reading per device per day for last 7 days with device status"""
        seven_days_ago = datetime.now() - timedelta(days=7)

        pipeline = [
            # Match readings from last 7 days
            {"$match": {"reading_time": {"$gte": seven_days_ago}}},

            # Join with sensors collection
            {"$lookup": {
                "from": "sensors",
                "localField": "sensor_id",
                "foreignField": "id",
                "as": "sensor"
            }},
            {"$unwind": "$sensor"},

            # Join with devices collection
            {"$lookup": {
                "from": "devices",
                "localField": "sensor.device_id",
                "foreignField": "id",
                "as": "device"
            }},
            {"$unwind": "$device"},

            # Extract date part
            {"$addFields": {
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$reading_time"}}
            }},

            # Group by device and day
            {"$group": {
                "_id": {
                    "device_id": "$device.id",
                    "day": "$day"
                },
                "device_name": {"$first": "$device.name"},
                "status": {"$first": "$device.status"},
                "avg_reading": {"$avg": "$reading_value"}
            }},

            # Project final fields
            {"$project": {
                "_id": 0,
                "device_id": "$_id.device_id",
                "device_name": 1,
                "status": 1,
                "day": "$_id.day",
                "avg_reading": 1
            }},

            # Sort results
            {"$sort": {"device_id": 1, "day": 1}}
        ]

        return list(self.db.sensor_readings.aggregate(pipeline))

    def get_sensor_extremes_per_device(self):
        """Sensor with max and min reading per device (optimized)"""

        # Base lookups & unwinds
        lookups = [
            {"$lookup": {
                "from": "sensors",
                "localField": "sensor_id",
                "foreignField": "id",
                "as": "sensor"
            }},
            {"$unwind": "$sensor"},
            {"$lookup": {
                "from": "devices",
                "localField": "sensor.device_id",
                "foreignField": "id",
                "as": "device"
            }},
            {"$unwind": "$device"},
        ]

        # Max‐reading pipeline
        max_pipeline = lookups + [
            {"$sort": {"device.id": 1, "reading_value": -1}},
            {"$group": {
                "_id": "$device.id",
                "device_id":    {"$first": "$device.id"},
                "device_name":  {"$first": "$device.name"},
                "sensor_id":    {"$first": "$sensor.id"},
                "sensor_type":  {"$first": "$sensor.type"},
                "reading_value":{"$first": "$reading_value"},
                "reading_time": {"$first": "$reading_time"}
            }},
            {"$addFields": {"rank_type": "MAX"}},
            {"$project": {"_id": 0}}
        ]

        # Min‐reading pipeline
        min_pipeline = lookups + [
            {"$sort": {"device.id": 1, "reading_value": 1}},
            {"$group": {
                "_id": "$device.id",
                "device_id":    {"$first": "$device.id"},
                "device_name":  {"$first": "$device.name"},
                "sensor_id":    {"$first": "$sensor.id"},
                "sensor_type":  {"$first": "$sensor.type"},
                "reading_value":{"$first": "$reading_value"},
                "reading_time": {"$first": "$reading_time"}
            }},
            {"$addFields": {"rank_type": "MIN"}},
            {"$project": {"_id": 0}}
        ]

        # Union and sort
        pipeline = [
            *max_pipeline,
            {"$unionWith": {
                "coll": "sensor_readings",
                "pipeline": min_pipeline
            }},
            {"$sort": {"device_id": 1, "reading_value": -1}}
        ]

        return list(self.db.sensor_readings.aggregate(pipeline))


    def get_avg_time_between_readings(self):
        """Average time between readings per sensor"""
        pipeline = [
            # Sort by sensor and timestamp
            {"$sort": {"sensor_id": 1, "reading_time": 1}},

            # Calculate time differences
            {"$setWindowFields": {
                "partitionBy": "$sensor_id",
                "sortBy": {"reading_time": 1},
                "output": {
                    "prev_time": {"$shift": {"output": "$reading_time", "by": -1}}
                }
            }},

            # Remove first reading (no previous)
            {"$match": {"prev_time": {"$ne": None}}},

            # Calculate time difference in seconds
            {"$addFields": {
                "time_diff_sec": {
                    "$divide": [
                        {"$subtract": ["$reading_time", "$prev_time"]},
                        1000  # Convert milliseconds to seconds
                    ]
                }
            }},

            # Calculate average per sensor
            {"$group": {
                "_id": "$sensor_id",
                "avg_seconds_between_readings": {"$avg": "$time_diff_sec"}
            }},

            # Project final fields
            {"$project": {
                "_id": 0,
                "sensor_id": "$_id",
                "avg_seconds_between_readings": 1
            }}
        ]

        return list(self.db.sensor_readings.aggregate(pipeline))
