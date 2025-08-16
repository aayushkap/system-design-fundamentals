#!/usr/bin/env bash
set -euo pipefail

# Wait utility
wait_for_ok() {
  local host=$1; local port=$2
  echo "Waiting for $host:$port ..."
  until mongosh --quiet --host "$host" --port "$port" --eval "db.runCommand({ ping: 1 })" >/dev/null 2>&1; do
    sleep 2
  done
}

# 1) Initiate Config RS
wait_for_ok cfg1 27019
wait_for_ok cfg2 27019
wait_for_ok cfg3 27019
mongosh --norc --quiet --host cfg1 --port 27019 <<'JS'
rs.initiate({
  _id: "cfgRS",
  configsvr: true,
  members: [
    { _id: 0, host: "cfg1:27019" },
    { _id: 1, host: "cfg2:27019" },
    { _id: 2, host: "cfg3:27019" }
  ]
})
JS

# 2) Initiate Shard 1 RS
wait_for_ok shard1a 27018
wait_for_ok shard1b 27018
wait_for_ok shard1c 27018
mongosh --norc --quiet --host shard1a --port 27018 <<'JS'
rs.initiate({
  _id: "shard1RS",
  members: [
    { _id: 0, host: "shard1a:27018" },
    { _id: 1, host: "shard1b:27018" },
    { _id: 2, host: "shard1c:27018" }
  ]
})
JS

# 3) Initiate Shard 2 RS
wait_for_ok shard2a 27018
wait_for_ok shard2b 27018
wait_for_ok shard2c 27018
mongosh --norc --quiet --host shard2a --port 27018 <<'JS'
rs.initiate({
  _id: "shard2RS",
  members: [
    { _id: 0, host: "shard2a:27018" },
    { _id: 1, host: "shard2b:27018" },
    { _id: 2, host: "shard2c:27018" }
  ]
})
JS

# 4) Add shards to mongos and enable sharding
wait_for_ok mongos 27017
mongosh --norc --quiet --host mongos --port 27017 <<'JS'
sh.addShard("shard1RS/shard1a:27018,shard1b:27018,shard1c:27018")
sh.addShard("shard2RS/shard2a:27018,shard2b:27018,shard2c:27018")

sh.enableSharding("bench")
// Choose a good shard key for write scaling and balanced distribution
// Here we use a compound hashed key: userId + createdAt
sh.shardCollection("bench.events", { userId: "hashed", createdAt: 1 })

// Helpful indexes for common queries
db.getSiblingDB("bench").events.createIndex({ createdAt: 1 })
db.getSiblingDB("bench").events.createIndex({ type: 1, createdAt: -1 })
JS

echo "✅ Sharded cluster initialized. Connect to mongodb://localhost:27017"