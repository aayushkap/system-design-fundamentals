# Databases

1.  Cassandra DB:

- Cassandra is a distributed NoSQL database designed to handle large amounts of data across many commodity servers, providing high availability with no single point of failure.

- It is particularly well-suited for applications that require scalability and high write throughput. You can easily enable data replication and partitioning (sharding) to ensure data is distributed across multiple nodes, for fault tolerance and performance.

- Cassandra uses a peer-to-peer architecture, meaning all nodes are equal and can handle read and write requests. This design allows for horizontal scaling by adding more nodes to the cluster.

- No server‑side _JOINs or GROUP BY_ - Cassandra Query Language (CQL) does not support GROUP BY across partitions or joins between tables. Aggregations must be done in language, after data retrieval.

2.  Clickhouse DB:

- A high-performance columnar database designed for real-time analytics on big data. It’s built to handle OLAP (Online Analytical Processing) workloads extremely fast— _billions_ of rows in milliseconds. Great for dashboards, reporting, and analytics applications.

- Since it is Columnar, it stores data in columns rather than rows. This allows for efficient data compression and faster query performance, because it only reads the necessary columns for a query.

- It has clustered architecture, allowing for distributed data processing across multiple nodes. This means you can scale horizontally by adding more nodes to handle larger datasets and more complex queries.

- Insert Now, Optimize Later - ClickHouse allows you to insert data without requiring immediate optimization. This means you can compress data into Materiazed Views later, which can significantly improve query performance.

- Engines: ClickHouse supports various table engines, such as MergeTree, which is optimized for high-speed inserts and efficient querying.

3.  TimescaleDB:

- TimescaleDB is an open-source time-series database built on top of PostgreSQL. It is designed to handle time-series data efficiently, making it ideal for applications that require high write throughput and complex queries on time-series data.

- In TimescaleDB, data is stored in hypertables, which are partitioned tables that allow for efficient storage and querying of time-series data. Each partition is a seperate table. This means you can handle large volumes of time-series data without sacrificing performance. TimescaleDB also supports advanced time-series functions, such as continuous aggregates (materialized views) and time-based partitioning.

- We can define retention policies to automatically drop old data, which is useful for managing storage in time-series applications. It also supports advanced indexing and compression techniques to optimize query performance.

4.  MongoDB:

- MongoDB is a NoSQL document database that stores data in flexible, JSON-like documents. It is designed for scalability and high availability, making it suitable for applications that require rapid development and iteration.

- MongoDB uses a flexible schema, allowing you to store data in a way that is easy to change and adapt as your application evolves. This is particularly useful for applications with evolving data models.

- It supports horizontal scaling through sharding, which allows you to distribute data across multiple nodes. It also provides built-in replication.

# About the demo

In this demo we will use sensor data as an example. The data will be generated using the Faker library, and inserted into the databases.

- devices: id (UUID), name (String), location (String), status (String)
- sensors: id (UUID), device_id (UUID), type (String)
- sensor_readings: id (UUID), sensor_id (UUID), reading_time (Timestamp), reading_value (Double)
- alerts: id (UUID), device_id (UUID), alert_time (Timestamp), alert_type (String), description (String)

## Test Queries

1.  Average Reading per Device per Day (for last 7 days), with Device Status

```sql
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
```

2. Sensor with Max and Min Reading per Device

```sql
SELECT *
FROM (
  SELECT
    d.id AS device_id,
    d.name AS device_name,
    s.id AS sensor_id,
    s.type AS sensor_type,
    sr.reading_value,
    sr.reading_time,
    RANK() OVER (PARTITION BY d.id ORDER BY sr.reading_value DESC) AS max_rank,
    RANK() OVER (PARTITION BY d.id ORDER BY sr.reading_value ASC) AS min_rank
  FROM devices d
  JOIN sensors s ON s.device_id = d.id
  JOIN sensor_readings sr ON sr.sensor_id = s.id
) ranked
WHERE max_rank = 1 OR min_rank = 1
ORDER BY device_id, reading_value DESC;
```

3. Average Time Between Readings per Sensor (Using LAG + TIMESTAMP DIFF)

```sql
WITH time_diffs AS (
  SELECT
    sr.sensor_id,
    sr.reading_time,
    LAG(sr.reading_time) OVER (PARTITION BY sr.sensor_id ORDER BY sr.reading_time) AS prev_time
  FROM sensor_readings sr
)
SELECT
  sensor_id,
  AVG(EXTRACT(EPOCH FROM (reading_time - prev_time))) AS avg_seconds_between_readings
FROM time_diffs
WHERE prev_time IS NOT NULL
GROUP BY sensor_id;
```

# Observations

1. Cassandar - Took the most amount of memory and time to insert data. it is also the slowest on reads and no aggregations. It is not suitable for time-series data, as it does not support time-based partitioning or advanced time-series functions. It is slow on reads.

2. Clickhouse - Easy to crash. Any failure during the insertions will result in a corrupted database. Only choice was to drop the table and recreate it.
