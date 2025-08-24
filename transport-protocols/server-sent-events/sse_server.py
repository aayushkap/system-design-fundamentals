from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
from faker import Faker
import uvicorn

app = FastAPI()
fake = Faker()

async def event_generator():
    counter = 0
    while counter < 10:
        counter += 1
        # SSE format: data: <message>\n\n
        yield f"data: {fake.word()}\n\n" # data keyword is required for SSE
        await asyncio.sleep(0.5)

@app.get("/sse")
async def sse_endpoint():
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
