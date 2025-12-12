import logging
from typing import List

from pydantic import BaseModel
from starlette.responses import RedirectResponse

from src.model.db_model import Runner
from src.repo.cross_repository import CrossRepository

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WarriorFit API",
    description="API for accessing the WarriorFit running event database",
    version="1.0.1",
    docs_url = "/docs" ,
    port = 8550
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("../app.log"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)




repo = CrossRepository()
class Recording(BaseModel):
    position: int
    time: float

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.get("/crosses")
async def get_crosses():
    return await repo.get_all_crosses()

@app.get("/crosses/{id_cross}")
async def get_cross(id_cross:int):
    return await repo.get_cross(id_cross)

@app.post("/crosses/{serial_number}/{id_cross}")
async def add_runner(serial_number:str, id_cross:int):
    return await repo.add_runner(serial_number, id_cross)

@app.get("/crosses/runners/{cross_id}")
async def get_runners(cross_id:int):
    return await repo.get_all_runners(cross_id)




@app.post("/crosses/runner/{serial_number}/{id_cross}")
async def add_runner(serial_number:str, id_cross:int):
    return await repo.add_runner(serial_number, id_cross)

# ... existing code ...

@app.post("/crosses/{cross_id}")
async def save_cross_recordings(cross_id: int, recordings: list[Recording]):
    runners:List[Runner] = []
    for recording in recordings:
        runners.append(Runner(running_time=recording.time, serial_number=None))

    return await repo.save_recordings(cross_id, runners)