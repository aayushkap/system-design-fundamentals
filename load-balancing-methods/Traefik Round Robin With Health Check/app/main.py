from fastapi import FastAPI, HTTPException, Request
import socket
import secrets # Secrets because has random seed, so different across the containers
from time import sleep

app = FastAPI()

@app.get("/")
async def root(request:Request):
    n = request.query_params.get("n")
    hostname = socket.gethostname()
    print(f"Service {hostname} Received: {n}")
    sleep(secrets.randbelow(3))
    return f"{hostname} got: {n}"

@app.get("/health")
async def health():
    if secrets.randbelow(4) == 0:
        print(f"[{socket.gethostname()}] Health check: UNHEALTHY")
        raise HTTPException(status_code=503, detail="Simulated failure")
    else:
        print(f"[{socket.gethostname()}] Health check: healthy")
        return {"status": "healthy"}
