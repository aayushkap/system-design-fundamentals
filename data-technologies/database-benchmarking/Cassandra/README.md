# Cassandra
---

- Cassandra is a distributed NoSQL database designed to handle large amounts of data across many commodity servers, providing high availability with no single point of failure.

- It is particularly well-suited for applications that require scalability and high write throughput. You can easily enable data replication and partitioning (sharding) to ensure data is distributed across multiple nodes, for fault tolerance and performance.

- Cassandra uses a peer-to-peer architecture, meaning all nodes are equal and can handle read and write requests. This design allows for horizontal scaling by adding more nodes to the cluster.

- No server‑side _JOINs or GROUP BY_ - Cassandra Query Language (CQL) does not support GROUP BY across partitions or joins between tables. Aggregations must be done in language, after data retrieval.