import threading
import requests
from collections import Counter, defaultdict

URL = 'http://localhost:8000'
NUM_CLIENTS = 3
NUM_REQUESTS = 20

results = defaultdict(Counter)
lock = threading.Lock()

def client_task(client_id):
    session = requests.Session()  # keep-alive
    for _ in range(NUM_REQUESTS):
        try:
            print(f"{client_id} -> requesting {URL}")
            resp = session.get(URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            instance = data.get('instance', 'unknown')
        except requests.HTTPError:
            instance = f'HTTP{resp.status_code}'
            print(f"{client_id} -> HTTP error {resp.status_code}")
        except ValueError:
            instance = 'INVALID_JSON'
            print(f"{client_id} -> invalid JSON in response")
        except Exception as e:
            instance = f'ERROR'
            print(f"{client_id} -> other error: {e}")
        with lock:
            results[client_id][instance] += 1

threads = []
for i in range(1, NUM_CLIENTS + 1):
    t = threading.Thread(target=client_task, args=(f'client{i}',))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

total = Counter()
print("\nPer-client results:")
for client, ctr in results.items():
    total.update(ctr)
    print(f"  {client}: {dict(ctr)}")

print("\nTotal across all clients:")
print(dict(total))
