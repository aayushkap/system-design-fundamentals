import os
from pymongo import MongoClient
from faker import Faker

class MongoDBClient:
    def __init__(self, uri="mongodb://localhost:27017/", db="iot"):
        self.client = MongoClient(uri)
        self.client = MongoClient(uri, uuidRepresentation="standard")
        self.db = self.client[db]

    def create_schema(self):
        # Mongo is schemaless; ensure indexes
        self.db.devices.create_index("id", unique=True)
        self.db.sensors.create_index("id", unique=True)
        self.db.sensor_readings.create_index([("sensor_id",1),("reading_time",1)])
        self.db.alerts.create_index("device_id")

    def insert_device(self, id, name, location, status):
        return self.db.devices.insert_one(dict(id=id, name=name, location=location, status=status))

    def insert_sensor(self, id, device_id, type_):
        return self.db.sensors.insert_one(dict(id=id, device_id=device_id, type=type_)).inserted_id

    def insert_reading(self, id, sensor_id, value, ts):
        self.db.sensor_readings.insert_one(dict(id=id, sensor_id=sensor_id, reading_value=value, reading_time=ts))

    def insert_alert(self, id, device_id, atype, ts, desc):
        self.db.alerts.insert_one(dict(id=id, device_id=device_id, alert_type=atype, alert_time=ts, description=desc))

    def get_all_tables(self):
        return self.db.list_collection_names()

    def execute_query(self, query):
        # MongoDB queries are typically done through the collection interface
        collection_name = query.get("collection")
        if not collection_name:
            raise ValueError("Query must specify a collection")
        collection = self.db[collection_name]
        return list(collection.find(query.get("filter", {}), query.get("projection", None)))