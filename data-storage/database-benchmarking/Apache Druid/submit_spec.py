import requests

specs = specs = [{
  "type": "index",
  "spec": {
    "dataSchema": {
      "dataSource": "devices",
      "timestampSpec": {
        "column": "!!!_dummy_!!!",
        "missingValue": "1970-01-01T00:00:00Z"
      },
      "dimensionsSpec": {
        "dimensions": [
          {"type": "string", "name": "id"},
          {"type": "string", "name": "name"},
          {"type": "string", "name": "location"},
          {"type": "string", "name": "status"}
        ]
      },
      "granularitySpec": {
        "queryGranularity": "NONE",
        "rollup": False,
        "segmentGranularity": "YEAR"
      }
    },
    "ioConfig": {
      "type": "index",
      "inputSource": {
        "type": "local",
        "files": ["/data/devices.csv"]  # Corrected to use 'files' array
      },
      "inputFormat": {
        "type": "csv",
        "findColumnsFromHeader": True,
        "skipHeaderRows": 0
      }
    },
    "tuningConfig": {
      "type": "index",
      "partitionsSpec": {
        "type": "dynamic"
      }
    }
  }
},
{
  "type": "index",
  "spec": {
    "dataSchema": {
      "dataSource": "sensors",
      "timestampSpec": {
        "column": "!!!_dummy_!!!",
        "missingValue": "1970-01-01T00:00:00Z"
      },
      "dimensionsSpec": {
        "dimensions": [
          {"type": "string", "name": "id"},
          {"type": "string", "name": "device_id"},
          {"type": "string", "name": "type"}
        ]
      },
      "granularitySpec": {
        "queryGranularity": "NONE",
        "rollup": False,
        "segmentGranularity": "YEAR"
      }
    },
    "ioConfig": {
      "type": "index",
      "inputSource": {
        "type": "local",
        "files": ["/data/sensors.csv"]  # Corrected to use 'files' array
      },
      "inputFormat": {
        "type": "csv",
        "findColumnsFromHeader": True,
        "skipHeaderRows": 0
      }
    },
    "tuningConfig": {
      "type": "index",
      "partitionsSpec": {
        "type": "dynamic"
      }
    }
  }
},
{
  "type": "index",
  "spec": {
    "dataSchema": {
      "dataSource": "sensor_readings",
      "timestampSpec": {
        "column": "reading_time",
        "format": "iso"
      },
      "dimensionsSpec": {
        "dimensions": [
          {"type": "string", "name": "id"},
          {"type": "string", "name": "sensor_id"},
          {"type": "double", "name": "reading_value"}
        ]
      },
      "granularitySpec": {
        "rollup": False,
          "segmentGranularity": "DAY",
          "queryGranularity": "MINUTE"
      }
    },
    "ioConfig": {
      "type": "index",
      "inputSource": {
        "type": "local",
        "files": ["/data/sensor_readings.csv"]  # Corrected to use 'files' array
      },
      "inputFormat": {
        "type": "csv",
        "findColumnsFromHeader": True,
        "skipHeaderRows": 0
      }
    },
    "tuningConfig": {
      "type": "index_parallel",
      "maxNumWorkers": 4,  # Adjust based on your system's capabilities
      "maxRowsInMemory": 500000,     # smaller in‑memory flushes
      "maxTotalRows": 500000,        # cap total rows before final persist
      "partitionsSpec": {
        "type": "dynamic"
      }
    }
  }
},
{
  "type": "index",
  "spec": {
    "dataSchema": {
      "dataSource": "alerts",
      "timestampSpec": {
        "column": "alert_time",
        "format": "iso"
      },
      "dimensionsSpec": {
        "dimensions": [
          {"type": "string", "name": "id"},
          {"type": "string", "name": "device_id"},
          {"type": "string", "name": "alert_type"},
          {"type": "string", "name": "description"}
        ]
      },
      "granularitySpec": {
        "queryGranularity": "NONE",
        "rollup": False,
        "segmentGranularity": "DAY"
      }
    },
    "ioConfig": {
      "type": "index",
      "inputSource": {
        "type": "local",
        "files": ["/data/alerts.csv"]  # Corrected to use 'files' array
      },
      "inputFormat": {
        "type": "csv",
        "findColumnsFromHeader": True,
        "skipHeaderRows": 0
      }
    },
    "tuningConfig": {
      "type": "index",
      "partitionsSpec": {
        "type": "dynamic"
      }
    }
  }
}]

for spec in specs:
    resp = requests.post(
        "http://localhost:8888/druid/indexer/v1/task",
        json=spec
    )
    print(resp.json())
