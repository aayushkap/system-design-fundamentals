Vitess is a tool for scaling MySQL horizontally through sharding, and also for abstracting MySQL clusters behind a single unified interface.

Keyspaces: logical databases (commerce, customer).

VSchema: tells Vitess how to shard (hash on uid).

vtcombo: bundles MySQL + vttablet. This includes mysql servers.

vtgate: single router (listen on 15306) — hides shards.

vitess-topo: stores metadata about the cluster (keyspaces, shards, tablets).

Replication: primary → replica tablets, managed by Vitess.