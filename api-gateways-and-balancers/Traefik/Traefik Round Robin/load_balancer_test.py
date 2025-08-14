# Expected Result should be that load balancer distributes requests evenly across the servers.
# One server will recieve odd requests and the other will receive even requests.
import requests
for i in range(1, 101):
    print(f"Sending request with n={i}")
    res = requests.get("http://localhost", params={"n": i})
    print(f"Sent {i}, Response: {res.text}")
