# TimescaleDB:

---

- TimescaleDB is an open-source time-series database built on top of PostgreSQL. It is designed to handle time-series data efficiently, making it ideal for applications that require high write throughput and complex queries on time-series data.

- In TimescaleDB, data is stored in hypertables, which are partitioned tables that allow for efficient storage and querying of time-series data. Each partition is a seperate table. This means you can handle large volumes of time-series data without sacrificing performance. TimescaleDB also supports advanced time-series functions, such as continuous aggregates (materialized views) and time-based partitioning.

- We can define retention policies to automatically drop old data, which is useful for managing storage in time-series applications. It also supports advanced indexing and compression techniques to optimize query performance.


### Results:

- **Insertion**: 1,000,000 rows in `~56 seconds` (with batch-inserts of 100,000, which was faster than 10,000 by ~1.5x).
- **Query 1**: Average readings per device per day in `~65 seconds`.
- **Query 2**: Max readings per device in `~85 seconds`.
- **Query 3**: Average time between readings in `~41 seconds`.

### Observations:

- Comes with all the benefits of PostgreSQL, including ACID compliance, SQL support, and a rich ecosystem of tools.

- Slow on insertion compared to some of the other databases, but this is expected due to the overhead of maintaining time-series data structures and indexes. Plus this is not meant for big data ingestion.

- Query performance is generally good, especially for time-series specific queries. The use of hypertables and continuous aggregates helps optimize query performance.

- Not suitable for OLAP or OLTP workloads. But it thrives on *append‑only* telemetry data, logs, IoT sensor data etc.