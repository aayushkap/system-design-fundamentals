# Key Concepts

1.  Replica Set

    - A group of MongoDB nodes that all hold the same data.

    - One Primary (accepts writes) + multiple Secondaries (copies, can serve reads).

    - This achieves redundancy + high availability.

2.  Sharded Cluster

    - Many Replica Sets together form a sharded cluster.

    - Config Servers (store metadata about which shard has what).

    - Mongos Routers (where the application connects) forward queries to the right shards.

```plain text
            +-------------+
            |   mongos    |
            +-------------+
                  |
        +---------+---------+
        |                   |
+----------------+   +----------------+
| Shard1RS       |   | Shard2RS       |
|  P (shard1a)   |   |  P (shard2a)   |
|  S (shard1b)   |   |  S (shard2b)   |
|  S (shard1c)   |   |  S (shard2c)   |
+----------------+   +----------------+
        |                   |
        \------> DATA <------/

```

Shard 1 (shard1a, shard1b, shard1c)

    - These 3 containers form a replica set called shard1RS.

    - One of them will be the primary, the others are secondaries.

Shard 2 (shard2a, shard2b, shard2c)

    - These 3 containers form another replica set (shard2RS).

    - Again, one primary, two secondaries.

---

In Any Shard:

```
mongosh "mongodb://localhost:27018"
rs.status()
```

Will give us the information about the sharded set. We can see which shard is primary, which are secondaries, and the data they hold.

In the `mongos` Router:

```
mongosh "mongodb://localhost:27017"
sh.status()
use bench
db.events.getShardDistribution()
```

Will give us the information about the entire sharded cluster, including the shards, their replica sets, and the data distribution.

To test redundancy and high availability:

```
docker stop shard1a
```

This will stop the primary of shard1RS. The replica set will automatically elect a new primary from the secondaries.
On starting shard1a again, it will rejoin the replica set as a secondary and begin to sync data.
