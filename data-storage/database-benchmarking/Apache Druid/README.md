## Apache Druid

---

- Designed for real‑time ingestion and sub‑second OLAP queries on large volumes of event‑driven data. Built to optimize large, **append‑only** datasets for sub‑second queries across trillions of rows.

- Druid is schema‐on‐write: you must tell it your dimensions, timestamps, and metrics before it builds the segment.

- Apache Druid is built as a collection of independently scalable, fault‑tolerant services

  - `Coordinator`: Monitors historical nodes, assigns data segments (partitions of data) and manages data retention.
  - `Overlord`: Receives ingestion tasks (streaming or batch), schedules them on middleManagers (or Indexer processes), and tracks their status.
  - `MiddleManager (Indexer)`: Executes ingestion tasks. For streaming jobs, it continuously consumes from sources like Kafka or Kinesis, creates “real‑time” segments, and publishes them to deep storage.
  - `Historical`: Hosts immutable, queryable segments. On startup—or when new segments appear—historicals pull data from deep storage (e.g., S3, HDFS), cache it locally, and serve queries against it.
  - `Deep Storage`: Shared file storage (S3, HDFS, Azure Blob) that holds every ingested segment for backup, recovery, and re‑balancing across historical nodes.

- Stores each column separately, enabling narrow scans and minimizing I/O for wide tables. Timestamp, dimension, and metric columns are independently encoded and compressed.

- Services can scale independently. We add more middle managers for ingestion throughput, more historicals for storage capacity, or more brokers for query operations.

- You can configure hot (real‑time), warm (historical), and cold (deep‑storage‑only) tiers to optimize cost vs. performance. You can also configure data retention policies to automatically delete old data.

### Results:

- **Insertion**: 10,000,000 rows in `~13 minutes`. Even with optimizations, Druid's ingestion speed was extremely slow. Druid's batch ingestion isn't optimized for speed. It's optimized for building compressed, immutable segments for future fast queries.
- **Query 1**: Average readings per device per day in `~20 seconds`. This excludes worker startup time.
- **Query 2**: Max readings per device in `~6 minutes`. This excludes worker startup time.
- **Query 3**: Average time between readings in `~3 minutes`. This excludes worker startup time.

### Observations:

- The ingestion process is difficult to setup. It does not support regular sql insertion by default, and requires you to build a ingestion spec to define how to ingest data. This process is not well documented, and can be quite confusing.

- Druid requires a time-stamp column to be present in each table, meaning that it is not suitable for all datasets. we need to add a dummy column to our dataset to make it work.

- The queries are much slower when compared to other databases. Starting the worker nodes takes around `10 seconds` for each query, which adds to the total query time.

- Druid is not a general-purpose OLAP database like ClickHouse or DuckDB.

  It is specifically designed for:
    - Real-time streaming ingestion (Kafka, Kinesis)

    - Sub-second queries over pre-aggregated, immutable time slices ("segments")

    - OLAP dashboards with billions of rows, but on limited dimensions

    - Low cardinality dimensions, lots of metrics