# app/main.py
from fastapi import FastAPI, Request

import socket

app = FastAPI()

@app.get("/")
async def root(request: Request):
    n = request.query_params.get("n")
    hostname = socket.gethostname()  # So we can identify which container handled it
    print(f"[{hostname}] Received: {n}")
    return f"{hostname} got: {n}"
