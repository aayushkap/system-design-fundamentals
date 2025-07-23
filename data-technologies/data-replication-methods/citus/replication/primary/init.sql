-- replication/primary/init.sql

-- Configure primary for replication
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET hot_standby = 'on';
ALTER SYSTEM SET listen_addresses = '*';

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'rep_pass';

-- Add pg_hba.conf entry using ALTER ROLE (works in PostgreSQL 14+)
ALTER ROLE replicator WITH LOGIN REPLICATION CONNECTION LIMIT -1;