#!/usr/bin/env python3
"""
End-to-end performance tester for:
  A) Vanilla PostgreSQL (with streaming replica behind)
  B) Citus distributed cluster (coordinator + 2 workers)

This version:
 - Postgres: id BIGSERIAL PRIMARY KEY
 - Citus:    id BIGSERIAL (no PK), so COPY can auto-fill it
 - Ensures `demo` DB exists on the Citus coordinator before proceeding.
"""

import os
import time
import random
import io
import psycopg2
from contextlib import contextmanager

# === CONFIGURATION ===

NUM_ROWS   = 10_000_000
COPY_BATCH = 50_000

PG_PRIMARY_DSN    = os.getenv(
    "PG_PRIMARY_DSN",
    "host=localhost port=5432 dbname=demo user=postgres password=secret"
)
CITUS_CONTROL_DSN = os.getenv(
    "CITUS_CONTROL_DSN",
    "host=localhost port=5433 dbname=postgres user=postgres password=secret"
)
CITUS_COORD_DSN   = os.getenv(
    "CITUS_COORD_DSN",
    "host=localhost port=5433 dbname=demo user=postgres password=secret"
)

QUERIES = {
    "count_all":           "SELECT count(*) FROM sensor_data;",
    "avg_value_by_sensor": "SELECT sensor_id, avg(value) FROM sensor_data GROUP BY sensor_id ORDER BY sensor_id;",
    "recent_100":          "SELECT * FROM sensor_data ORDER BY timestamp DESC;"
}


@contextmanager
def get_conn(dsn):
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()


def ensure_citus_demo_db():
    """Creates the demo DB on Citus if it doesn't already exist."""
    with get_conn(CITUS_CONTROL_DSN) as ctrl:
        with ctrl.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'demo';")
            if cur.fetchone():
                print("✔ Citus demo database already exists")
            else:
                print("→ Creating Citus demo database")
                cur.execute("CREATE DATABASE demo;")
                print("✔ Created Citus demo database")
            
            cur.execute("CREATE INDEX ON sensor_data (timestamp DESC);")


def setup_table(pg_conn, distributed=False):
    """
    Drops & recreates sensor_data.
    - Plain Postgres: id BIGSERIAL PRIMARY KEY
    - Citus:         id BIGSERIAL (no PK), then distributed on sensor_id
    """
    with pg_conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS sensor_data;")

        if not distributed:
            print("→ Creating plain Postgres table with PRIMARY KEY")
            cur.execute("""
                CREATE TABLE sensor_data (
                    id         BIGSERIAL PRIMARY KEY,
                    sensor_id  INT       NOT NULL,
                    timestamp  TIMESTAMPTZ NOT NULL,
                    value      DOUBLE PRECISION NOT NULL
                );
            """)
        else:
            print("→ Creating Citus-distributed table (id BIGSERIAL, no PK)")
            cur.execute("""
                CREATE TABLE sensor_data (
                    id         BIGSERIAL,
                    sensor_id  INT         NOT NULL,
                    timestamp  TIMESTAMPTZ NOT NULL,
                    value      DOUBLE PRECISION NOT NULL
                );
            """)
            cur.execute("CREATE EXTENSION IF NOT EXISTS citus;")
            cur.execute("SELECT create_distributed_table('sensor_data','sensor_id');")

    print(f"✔ {'Citus' if distributed else 'Postgres'} table set up")


def bulk_insert(pg_conn, num_rows, batch_size=COPY_BATCH):
    total = 0
    t0 = time.time()
    batches = (num_rows + batch_size - 1) // batch_size

    for b in range(batches):
        this_batch = min(batch_size, num_rows - total)
        buf = io.StringIO()
        for _ in range(this_batch):
            sid    = random.randint(1, 100)
            ts     = time.time() - random.random() * 365 * 24 * 3600
            ts_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))
            val    = random.random() * 100.0
            buf.write(f"{sid}\t{ts_iso}\t{val}\n")
        buf.seek(0)

        with pg_conn.cursor() as cur:
            # `Copy from`` is the fastest way to insert large amounts of data in pg
            # It reads direcly from a the in-memory buffer in one short, inserting all rows at once
            cur.copy_from(buf, "sensor_data", columns=("sensor_id","timestamp","value"))

        total += this_batch
        if (b+1) % 5 == 0 or b == batches-1:
            print(f"  Inserted {total}/{num_rows} rows in {time.time()-t0:.1f}s")

    print(f"✔ Bulk insert of {total} rows done in {time.time()-t0:.1f}s")


def run_queries(pg_conn):
    timings = {}
    for name, sql in QUERIES.items():
        with pg_conn.cursor() as cur:
            t0 = time.time()
            cur.execute(sql)
            rows = cur.fetchall()
            dt = time.time() - t0
            timings[name] = dt
            print(f"→ {name:20} took {dt:.3f}s, returned {len(rows)} rows")
            if name != "count_all" and rows:
                for sample in rows[:3]:
                    print("   ", sample)
    return timings


def main():
    summary = {}

    # 1) Vanilla Postgres
    print("\n=== Testing vanilla PostgreSQL ===")
    with get_conn(PG_PRIMARY_DSN) as pg:
        # setup_table(pg, distributed=False)
        # bulk_insert(pg, NUM_ROWS)
        summary['postgres'] = run_queries(pg)

    # 2) Prepare Citus
    print("\n=== Ensuring Citus demo DB exists ===")
    ensure_citus_demo_db()

    print("\n=== Testing Citus distributed cluster ===")
    with get_conn(CITUS_COORD_DSN) as citus:
        # setup_table(citus, distributed=True)
        # bulk_insert(citus, NUM_ROWS)
        summary['citus'] = run_queries(citus)

    # 3) Summary
    print("\n=== SUMMARY (seconds) ===")
    print(f"{'Query':20} | {'Postgres':>8} | {'Citus':>8}")
    print("-" * 40)
    for name in QUERIES:
        p = summary['postgres'][name]
        c = summary['citus'][name]
        winner = "Citus" if c < p else "Postgres"
        print(f"{name:20} | {p:8.3f} | {c:8.3f}   ← {winner}")

    print("\nAll done.")


if __name__ == "__main__":
    main()
