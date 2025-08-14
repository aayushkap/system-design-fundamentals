## InfluxDB 2

---

- Influx DB is Columnar storage designed specifically for time-series data like metrics, IoT sensor readings, logs, events, etc. It is capable of handeling Handle high write throughput, efficient compression, and quick time-based queries.

- Measurements are the core data structure in InfluxDB, similar to tables in relational databases. Each measurement can have multiple `Fields` (key-value pairs) and `Tags` (indexed metadata). Indexing tags allows for fast querying and filtering.

- Data gets stored in a line protocol format. Each line represents a single data point with a timestamp, measurement name, tags, and fields. For example:

  ```
  sensor_readings,sensor_id=xyz789,device_id=abc123 value=23.5 1691990400000000000
  <|measurement|,|tag_key=tag_value| field_key=field_value |timestamp|>
  ```

- Influx stores tags and fields separately, when we want “device name + sensor reading + aggregated value”, we have to:

```
1. Pull devices (device_id, name)

2. Pull sensors (sensor_id, device_id)

3. Pull readings (sensor_id, device_id, value, _time)

4. Join tables via device_id or sensor_id

5. Aggregate or group as needed
```

- Influx DB 2 adds a new query language called Flux, which is more powerful and flexible than the previous InfluxQL. It allows for complex queries, data transformations, and aggregations.

- The open-source version of InfluxDB 2 does not support clustering or high availability. It is designed for single-node deployments. For distributed setups, InfluxDB Enterprise is required. By default, InfluxDB 2 shards data by time intervals, which helps with performance and retention policies.

### Results:

- **Insertion**: 10,000,000 rows in `~189.14 seconds` (with batch-inserts of 500,000).
- **Query 1**: Average readings per device per day in `~0.09 seconds`.
- **Query 2**: Max readings per device in `~1.15 seconds`.
- **Query 3**: Average time between readings in `~2.68 seconds`.

### Observations:

- The UI is highly intuitive and allows easy exploration of data.

- Decent write performance, especially with large batch sizes. Although not as impressive as some other databases like ClickHouse, it still handles high write well.

- Query performance is generally very good, especially for time-based queries. Flux provides a lot of flexibility for complex queries. However the language comes with a learning curve and is not as straightforward as SQL (solved with Influx DB 3).

- With the inbuilt retention policies and data lifecycle management, it is easy to manage data over time, making influxDB a good choice for long-term time-series data storage and analysis.
