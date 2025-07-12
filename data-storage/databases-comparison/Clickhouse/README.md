## Clickhouse DB:

---

- A high-performance columnar database designed for real-time analytics on big data. It’s built to handle OLAP (Online Analytical Processing) workloads extremely fast— _billions_ of rows in milliseconds. Great for dashboards, reporting, and analytics applications.

- Since it is Columnar, it stores data in columns rather than rows. This allows for efficient data compression and faster query performance, because it only reads the necessary columns for a query.

- It has clustered architecture, allowing for distributed data processing across multiple nodes. This means you can scale horizontally by adding more nodes to handle larger datasets and more complex queries.

- Insert Now, Optimize Later - ClickHouse allows you to insert data without requiring immediate optimization. This means you can compress data into Materiazed Views later, which can significantly improve query performance. This is done via a background process.

- Engines: ClickHouse supports various table engines, such as MergeTree, which is optimized for high-speed inserts and efficient querying.

### Results:

- **Insertion**: 10,000,000 rows in `~89 seconds` (with batch-inserts of 100,000). This can be further optimized by playing with the `max_insert_block_size` parameter and batch size.
- **Query 1**: Average readings per device per day in `~0.06 seconds`.
- **Query 2**: Max readings per device in `~3.42 seconds`.
- **Query 3**: Average time between readings in `~0.43 seconds`.

### Observations:

- Absolutely thrives on bulk inserts. Can handle millions of rows in seconds.

- When properly optimized using MergeTree, Denormalized (Flattened) data and Materiazed Views, it can achieve sub-second query times even on massive datasets. When tested on 10,000,000 rows, it returned results to complex queries in under 1 second.

- Since it is Columnar, it only has to look at relavent columns to run massive calculations, which is why it can achieve such high speeds.
