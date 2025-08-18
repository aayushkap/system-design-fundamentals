import os, time, random, string
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING

MONGO_URI = "mongodb://localhost:27017"
DB = "bench"
COLL = "events"
TOTAL = 1_000_000
BATCH = 10_000
USERS = 1_000

client = MongoClient(MONGO_URI)
coll = client[DB][COLL]

print(f"Connecting to {MONGO_URI} ...")
coll.database.command("ping")
print("Connected. Inserting...")

start = time.time()
base = datetime.utcnow() - timedelta(days=30)

def rand_user():
    return random.randint(1, USERS)

def rand_type():
    return random.choice(["click", "view", "purchase", "signup", "scroll"])

def rand_payload():
    return {
        "ref": ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
        "val": random.random(),
        "ok": random.choice([True, False])
    }

inserted = 0
while inserted < TOTAL:
    batch = []
    for _ in range(min(BATCH, TOTAL-inserted)):
        ts = base + timedelta(seconds=random.randint(0, 30*24*3600))
        doc = {
            "userId": rand_user(),
            "createdAt": ts,
            "type": rand_type(),
            "payload": rand_payload()
        }
        batch.append(doc)
    res = coll.insert_many(batch, ordered=False)
    inserted += len(res.inserted_ids)
    if inserted % (BATCH*10) == 0:
        elapsed = time.time() - start
        rate = inserted/elapsed
        print(f"Inserted {inserted}/{TOTAL} docs @ {rate:,.0f} docs/s")

elapsed = time.time() - start
print(f"Inserted {inserted} docs in {elapsed:.1f}s ({inserted/elapsed:,.0f} docs/s)")

# Simple query to get the count of documents
count = coll.count_documents({})
print(f"Total documents in collection: {count}")