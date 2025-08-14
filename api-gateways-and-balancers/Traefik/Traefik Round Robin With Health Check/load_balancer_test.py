import requests
from concurrent.futures import ThreadPoolExecutor
import threading

def send_request(i):
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    print(f"[{thread_name} | ID: {thread_id}] Sending request n={i}")
    res = requests.get("http://localhost", params={"n": i})
    print(f"[{thread_name} | ID: {thread_id}] Sent n={i}, Response: {res.text}")

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(send_request, range(1, 101))
