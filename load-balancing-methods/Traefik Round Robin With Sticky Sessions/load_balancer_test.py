import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, OrderedDict

NUM_CLIENTS = 4
REQS_PER_CLIENT = 25
COOKIE_NAME = "app_session"

def session_worker(client_id):
    print(f"Client {client_id} starting session...")
    session = requests.Session()
    results = []  # will hold (n, hostname, cookie) triples
    last_cookie = None

    for i in range(1, REQS_PER_CLIENT + 1):
        resp = session.get("http://localhost", params={"n": i})
        data = resp.json()
        hostname = data["hostname"]

        cookie = session.cookies.get(COOKIE_NAME)

        results.append((i, hostname, cookie))
        last_cookie = cookie

    return client_id, results

if __name__ == "__main__":
    all_results = {}

    with ThreadPoolExecutor(max_workers=NUM_CLIENTS) as pool:
        # A future is a placeholder for the result of an asynchronous operation
        # Here we submit multiple tasks to the pool, each representing a client session
        futures = [pool.submit(session_worker, cid)
                   for cid in range(1, NUM_CLIENTS + 1)]
        for fut in as_completed(futures):
            cid, res = fut.result()
            all_results[cid] = res

    print("All requests completed.")
    for cid in sorted(all_results):
        res = all_results[cid]
        # OrderedDict to preserve order of first-seen cookies
        cookie_map = OrderedDict()
        for n, hostname, cookie in res:
            if cookie not in cookie_map:
                cookie_map[cookie] = {
                    "hostname": hostname,
                    "requests": []
                }
            cookie_map[cookie]["requests"].append(n)

        print(f"\nClient {cid}:")
        for cookie, info in cookie_map.items():
            h = info["hostname"]
            nums = info["requests"]
            print(f"Backend '{h}' via cookie '{cookie}': requests {nums[0]}–{nums[-1]} (total {len(nums)})")
