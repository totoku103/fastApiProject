import asyncio

from fastapi import FastAPI
from starlette.responses import StreamingResponse

app = FastAPI()


data_store = {}
data_lock = asyncio.Lock()


@app.get("/sse/{key}")
async def sse(key: str):
    async def event_generator():
        while True:
            async with data_lock:
                if key in data_store:
                    yield f"data: {data_store[key]}\n\n"
                    data_store.pop(key)
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/data/{key}/{value}")
async def set_data(key: str, value: str):
    async with data_lock:
        data_store[key] = value
    return {"message": "data set"}
