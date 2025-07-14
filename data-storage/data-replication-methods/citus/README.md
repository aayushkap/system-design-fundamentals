**Sharding** and **Replication** using PostgreSQL for replication and Citus for sharding.

---

- **Replication:**  
  Copying data to multiple nodes for high availability and read scalability.

- **Sharding:**  
  Partitioning data across nodes for write scalability and distributed storage.

- **Citus:**  
  A PostgreSQL extension that enables sharding and distributed query execution.

---

- By default, Citus creates **32 shards** per distributed table.  
  These shards are logical partitions of a table, distributed evenly across worker nodes.

- In this demo, the number of shards is set to **4** in the `init.sql` file for easier visualization of data distribution.

- **Workers** (Postgres containers) are where physical shards reside.  
  Adding more workers increases parallelism and storage capacity.

- The **Coordinator** node holds only metadata (the catalog of shards and their locations). Via the Coordinator, we can query and manage the distributed data seamlessly, as if it were a single PostgreSQL instance.

---

```plaintext
          ┌─────────────────┐
          │  Coordinator    │   ← metadata only
          └─────────────────┘
                   │
   ┌───────────────┼───────────────┐
   ▼               ▼               ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Worker1 │     │ Worker2 │ ... │ WorkerN │
│         │     │         │     │         │
│ Shard A ├──┐  │ Shard C │     │ Shard G │
│ Shard B │  │  │ Shard D │     │ Shard H │
└─────────┘  └─>└─────────┘<─┐  └─────────┘
                             │
            replicated copies│ if we set `replication_factor`
```

---

## Demo

```bash
docker exec -it citus-citus-coordinator-1 psql -U postgres -d postgres
```

---

**Number of Workers:**

```sql
SELECT *
  FROM pg_dist_node;
```

**Number of Shards:**

```sql
SELECT count(*) AS total_shard_placements
  FROM citus_shards;
```

**Shard Distribution Across Workers:**

```sql
SELECT
  nodename,
  count(*) AS shard_placements
FROM citus_shards
GROUP BY nodename
ORDER BY shard_placements DESC;
```

**Number Of Rows Per Shard:**

Use the `run_command_on_shards` function to execute a command on each shard independently.

```sql
SELECT cs.shard_name, r.result::int AS row_count
FROM run_command_on_shards('sensor_data', 'SELECT count(*) FROM %s') r 
JOIN citus_shards cs ON r.shardid = cs.shardid
WHERE cs.table_name = 'sensor_data'::regclass AND r.success = true
ORDER BY cs.shard_name;
```