from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def root(request: Request):
    http_version = request.scope.get("http_version")
    print(f"Incoming request over HTTP/{http_version}")
    return {"message": f"Hello from HTTP/{http_version}!"}
