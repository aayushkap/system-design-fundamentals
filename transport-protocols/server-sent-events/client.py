import requests

url = "http://127.0.0.1:8000/sse"

res = ""
with requests.get(url, stream=True) as response:
    for line in response.iter_lines():
        if line:
            data = line.decode("utf-8").strip()
            res += data[5:]
            print(f"Received: {data}")

print(f"Final result: {res}")
