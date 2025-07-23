#!/usr/bin/env bash
set -eux

# Give containers a bit of time to register with ZooKeeper
sleep 10

for host in mysql-s1-primary mysql-s1-replica mysql-s2-primary mysql-s2-replica; do
  until mysql -h "$host" -uroot -proot -e "SELECT 1" 2>/dev/null; do
    echo "Waiting for $host to be ready..."
    sleep 2
  done
  echo "$host is ready"
done

# Set up replication user on all MySQL instances
for host in mysql-s1-primary mysql-s1-replica mysql-s2-primary mysql-s2-replica; do
  mysql -h "$host" -uroot -proot -e "CREATE USER 'repl'@'%' IDENTIFIED BY 'repl'; GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';"
done

# 1. Create two keyspaces: `commerce` (sharded) and `customer` (unsharded)
vtctlclient -server vtctld:15999 CreateKeyspace commerce
vtctlclient -server vtctld:15999 CreateKeyspace customer

vtctlclient -server vtctld:15999 InitShardPrimary commerce/0000-8000 zone1-0000000100
vtctlclient -server vtctld:15999 InitShardPrimary commerce/8000-10000 zone1-0000000200

# 2. Define sharding & tables in JSON
cat << 'EOF' > commerce_vschema.json
{
  "sharded": true,
  "vindexes": {
	"hash_index": { "type": "hash" }
  },
  "tables": {
	"orders": {
	  "column_vindexes": [
		{ "column": "uid", "name": "hash_index" }
	  ]
	}
  }
}
EOF

cat << 'EOF' > customer_vschema.json
{
  "sharded": false,
  "tables": {
	"users": {}
  }
}
EOF

# 3. Apply VSchema
vtctlclient -server vtctld:15999 ApplyVSchema -vschema_file commerce_vschema.json commerce
vtctlclient -server vtctld:15999 ApplyVSchema -vschema_file customer_vschema.json customer

# 4. Rebuild Vitess serving graph so vtgate can route queries
vtctlclient -server vtctld:15999 RebuildKeyspaceGraph commerce
vtctlclient -server vtctld:15999 RebuildKeyspaceGraph customer
