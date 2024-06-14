import asyncio
import datetime
import json
from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, CursorResult

username = "totoku103"
password = quote_plus("totoku103")
host = "192.168.0.2"
database_name = "test"

DATABASE_URL = f"mysql+pymysql://{username}:{password}@{host}/{database_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()


class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=200), index=True)
    description = Column(String(length=200), index=True)


Base.metadata.create_all(bind=engine)


# Pydantic 스키마 정의
class ItemCreate(BaseModel):
    name: str
    description: str


class Item(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/1")
def insert(session: Session = Depends(get_db)):
    for i in range(10):
        model = ItemModel(name=f'item {datetime.datetime.now()}',
                          description=f'item {datetime.datetime.now()} description')
        session.add(model)

    session.commit()


@app.get("/sse/{param}")
async def sse(param: int,
              request: Request,
              session: Session = Depends(get_db)):
    client_host = request.client.host
    client_port = request.client.port
    client_connect_time = datetime.datetime.now()
    print(f"Client connected: {client_host}:{client_port} {client_connect_time}")

    async def get_data():
        try:
            while True:
                # items = session.query(ItemModel).all()
                # data = [Item.model_validate(item).model_dump() for item in items]
                from sqlalchemy import text
                execute: CursorResult = session.execute(text("select now()"))
                result = execute.cursor.fetchone()
                now_datetime = result[0]

                total_seconds = (now_datetime - client_connect_time).total_seconds()

                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                data = {
                    'param': param,
                    # 'client_host': client_host,
                    # 'client_port': client_port,
                    'start_datetime': client_connect_time.strftime(format="%Y-%m-%d %H:%M:%S"),
                    'now_datetime': now_datetime.strftime(format="%Y-%m-%d %H:%M:%S"),
                    'hours': hours,
                    'minutes': minutes,
                    'seconds': round(seconds, 2),
                    'total_seconds': round(total_seconds, 2)
                }
                yield f"data: {json.dumps(data)}\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"Client disconnected: {client_host}:{client_port}")

    return StreamingResponse(get_data(), media_type="text/event-stream")


@app.get("/sse2")
def sse2(session: Session = Depends(get_db)):
    d = session.query(ItemModel).first()
    return d
