#!/usr/bin/env bash
set -e

# Wait for initdb to finish, then append our replication entry:
cat >> "$PGDATA/pg_hba.conf" <<EOF
# Allow replication connections from any IP using md5
host    replication     replicator      0.0.0.0/0               md5
EOF
