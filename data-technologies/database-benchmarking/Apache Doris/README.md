## Apache Doris:

---

- Ultra high performance OLAP database. Sub-second query times on massive datasets.

- Especially optimized for analytical queries for BI tools. Uses Massive Parallel Processing (MPP) architecture with a columnar storage format. Utilizes vectorized query execution (which means it processes data in batches, which is much faster than row-based processing).

- Supports real-time data ingestion and supports all mysql protocols for easy integration. Also supports Materialized Views, which can pre-aggregate data for faster query performance.

### Results:

- **Insertion**: 10,00,000 rows in `~89 seconds` (with batch-inserts of 100,000).
- **Query 1**: Average readings per device per day in `~0.06 seconds`.
- **Query 2**: Max readings per device in `~3.42 seconds`.
- **Query 3**: Average time between readings in `~0.43 seconds`.

### Observations:

- Much more resource intensive than other databases, especially during the initial data load. It requires a lot of memory and CPU resources to perform optimally, unlike ClickHouse which was much more performant on the same hardware.

- Slow on bulk inserts.