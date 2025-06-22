import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict
from time import sleep
import random

NUM_WORKERS = 1000
REQUESTS_PER_WORKER = 1
TARGET_URL = "http://localhost:80"

# Shared, thread‑safe results
results = defaultdict(list)
lock = threading.Lock()

def send_single(worker_id, n):
    try:
        
        res = requests.get(TARGET_URL, params={"n": n})
        data = res.json()
        instance = data.get("instance", "unknown")
    except Exception as e:
        print(f"[Worker {worker_id}] Error on request {n}: {e}")
        instance = "error"
    with lock:
        results[(worker_id, instance)].append(n)

def send_batch(worker_id):

    print(f"[Worker {worker_id}] Starting batch of {REQUESTS_PER_WORKER} requests")
    with ThreadPoolExecutor(max_workers=REQUESTS_PER_WORKER) as inner:
        # schedule REQUESTS_PER_WORKER calls of send_single
        futures = [
            inner.submit(send_single, worker_id, n)
            for n in range(1, REQUESTS_PER_WORKER + 1)
        ]
        # optional: wait for all to finish
        for _ in as_completed(futures):
            pass
    print(f"[Worker {worker_id}] Batch complete")

if __name__ == "__main__":
    # Top‑level executor with NUM_WORKERS workers
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(send_batch, range(1, NUM_WORKERS + 1))

    # Summarize
    print("\nAll workers done.\nDistribution of requests:")
    # Group by instance ignoring worker_id
    combined = defaultdict(list)
    for (worker_id, instance), nums in results.items():
        combined[instance].extend(nums)
        print(f"  Worker {worker_id}, instance {instance}: {len(nums)} reqs")
    print("\nTotals per instance:")
    for instance, nums in combined.items():
        print(f"  • {instance}: {len(nums)} requests")
        
    print("\n Total requests sent:", sum(len(nums) for nums in combined.values()))
