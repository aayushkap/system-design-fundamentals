-- sharding/coordinator/init.sql
-- Enable Citus extension
CREATE EXTENSION citus;

-- Add worker nodes to cluster
SELECT citus_add_node('citus-worker1', 5432);
SELECT citus_add_node('citus-worker2', 5432);

SET citus.shard_count = 4; -- Number of shards to 4, across all workers
SET citus.shard_replication_factor = 2; -- Replication factor to 2, meaning 1 replica across workers

-- Create distributed table
DROP TABLE IF EXISTS sensor_data;
CREATE TABLE sensor_data (
	id BIGSERIAL,
	sensor_id INT,
	timestamp TIMESTAMPTZ,
	value FLOAT
);

-- Distribute table by sensor_id
-- 4 shards will be created for the sensor_data table
-- We can set replication factor to 2 if we want to replicate data across nodes. So different workers will have copies of the same shard.
SELECT create_distributed_table('sensor_data', 'sensor_id');

-- Insert sample data (distributed across workers)
INSERT INTO sensor_data (sensor_id, timestamp, value)
SELECT
	floor(random() * 100) + 1,
	now() - (random() * interval '365 days'),
	random() * 100
FROM generate_series(1, 1000);

-- Verify shard distribution
SELECT * FROM citus_shards;