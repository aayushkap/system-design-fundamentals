-- Enable Citus extension
CREATE EXTENSION citus;

-- Add worker nodes to cluster
SELECT citus_add_node('citus-worker1', 5432);
SELECT citus_add_node('citus-worker2', 5432);

-- Create distributed table
CREATE TABLE sensor_data (
    id BIGSERIAL,
    sensor_id INT,
    timestamp TIMESTAMPTZ,
    value FLOAT
);

-- Distribute table by sensor_id
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