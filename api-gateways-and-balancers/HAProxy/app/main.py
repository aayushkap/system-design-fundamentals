from fastapi import FastAPI
import os

app = FastAPI()
@app.get("/health")
async def health():
    return {"status": "ok", "instance": os.getenv("INSTANCE", "unknown")}
@app.get("/")
async def root():
    import time
    import random
    time.sleep(random.uniform(0.5, 1))
    return {"hello": "world", "instance": os.getenv("INSTANCE", "unknown")}
