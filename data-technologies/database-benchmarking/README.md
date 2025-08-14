# About the demo

In this demo, we use synthetic IoT sensor data generated to benchmark various databases. Scripts are provided to generate the data and perform the benchmarks.

Schema:

- **devices**: `id` (UUID), `name` (String), `location` (String), `status` (String)
- **sensors**: `id` (UUID), `device_id` (UUID), `type` (String)
- **sensor_readings**: `id` (UUID), `sensor_id` (UUID), `reading_time` (Timestamp), `reading_value` (Double)
- **alerts**: `id` (UUID), `device_id` (UUID), `alert_time` (Timestamp), `alert_type` (String), `description` (String)

## Test Queries

1. **Average Reading per Device per Day (last 7 days) with Device Status**

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

2. **Sensor with Max and Min Reading per Device**

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

3. **Average Time Between Readings per Sensor**

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

## Summary Statistics

| Database                          | Insertion Time         | Query 1 Time | Query 2 Time    | Query 3 Time    |
| --------------------------------- | ---------------------- | ------------ | --------------- | --------------- |
| [Apache Doris](./Apache%20Doris/) | \~243.9 s (1 M rows)   | \~0.22 s     | \0.1 s          | \~0.44 s        |
| [Apache Druid](./Apache%20Druid/) | \~780 s (10 M rows)    | \~20 s       | \~360 s (6 min) | \~180 s (3 min) |
| [Cassandra](./Cassandra/)         | \~180 s (10 M rows)    | N/A          | N/A             | N/A             |
| [ClickHouse](./Clickhouse/)       | \~89 s (10 M rows)     | \~0.06 s     | \~3.42 s        | \~0.43 s        |
| [MongoDB](./Mongo/)               | \~157.16 s (10 M rows) | 27.94 s      | >300 s (>5 min) | \~30.28 s       |
| [TimescaleDB](./Timescale%20DB/)  | \~56 s (1 M rows)      | 65 s         | 85 s            | 41 s            |
| [InfluxDB 2](./Influx%20DB%202/) | \~189 s (10 M rows)    | ~0.09 s      | \~1.15 s        | \~2.68 s        |

## Table of Contents

#### [Apache Doris](./Apache%20Doris/)

#### [Apache Druid](./Apache%20Druid/)

#### [Cassandra](./Cassandra/)

#### [ClickHouse](./Clickhouse/)

#### [MongoDB](./Mongo/)

#### [TimescaleDB](./Timescale%20DB/)

#### [InfluxDB 2](./Influx%20DB%202/)
