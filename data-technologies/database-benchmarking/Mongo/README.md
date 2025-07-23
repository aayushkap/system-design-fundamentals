## MongoDB:

- MongoDB is a NoSQL document database that stores data in flexible, JSON-like documents. It is designed for scalability and high availability, making it suitable for applications that require rapid development and iteration.

- MongoDB uses a flexible schema, allowing you to store data in a way that is easy to change and adapt as your application evolves. This is particularly useful for applications with evolving data models.

- It supports horizontal scaling through sharding, which allows you to distribute data across multiple nodes. It also provides built-in replication.

- Pipelines in MongoDB allow for complex data processing and aggregation, enabling you to perform operations like filtering, grouping, and sorting on large datasets.

### Results:

- **Insertion**: 10,000,000 rows in `~157.16 seconds` (with batch-inserts of 10,000).
- **Queries**:
  - Average readings per device per day: `27.94 seconds`
  - Max readings per sensor per device: `More than 5 minutes`
  - Average time between readings: `~30.28 seconds`

## Observations:

- Bulk inserts are effective, however they do not scale wil the buffer size. I achieved the best performance with a batch size of 10,000. The insert speed slowed down on both increasing the batch size and decreasing it below 10,000.

- Performance of analytical queries is somewhat acceptable, although certain queries, such as the max readings per sensor per device, can take a long time to execute.

- Definitely not the best choice for OLAP workloads, perhaps its better suited for long-term storage, as Mongo has great support for sharding and replication.

- The query language is powerful, but complex queries can become difficult to manage and optimize, especially when their are multiple stages and lookups involved.
