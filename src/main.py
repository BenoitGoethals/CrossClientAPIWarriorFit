import logging
from typing import List

from starlette.responses import RedirectResponse

from src.model.db_model import Runner
from src.model.schemas import (
    CrossResponse, CrossCreate, RunnerResponse,
    RunnerCreate, UnitResponse, UnitCreate
)
from src.repo.cross_repository import CrossRepository
from src.core.config_reader import get_config

from fastapi import FastAPI, Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(await request.body())}
    )

# API Key Security
config = get_config()
API_KEY = config.api.secret_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key

repo = CrossRepository()

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.get("/crosses", response_model=List[CrossResponse], dependencies=[Security(verify_api_key)])
async def get_crosses():
    return await repo.get_all_crosses()

@app.get("/crosses/{id_cross}", response_model=CrossResponse, dependencies=[Security(verify_api_key)])
async def get_cross(id_cross: int):
    return await repo.get_cross(id_cross)

@app.post("/crosses/{serial_number}/{id_cross}", dependencies=[Security(verify_api_key)])
async def add_runner(serial_number:str, id_cross:int):
    return await repo.add_runner(serial_number, id_cross)

@app.get("/crosses/runners/{cross_id}", response_model=List[RunnerResponse], dependencies=[Security(verify_api_key)])
async def get_runners(cross_id: int):
    return await repo.get_all_runners(cross_id)



@app.post("/crosses/runner/{serial_number}/{id_cross}", dependencies=[Security(verify_api_key)])
async def add_runner(serial_number:str, id_cross:int):
    return await repo.add_runner(serial_number, id_cross)

@app.post("/crosses/{cross_id}", dependencies=[Security(verify_api_key)])
async def save_cross_recordings(cross_id: int, recordings: List[RunnerCreate]):
    logger.info(f"Received POST request to /crosses/{cross_id}")
    logger.info(f"Number of recordings: {len(recordings)}")
    logger.info(f"Recordings data: {recordings}")

    runners: List[Runner] = []
    for recording in recordings:
        runners.append(Runner(running_time=recording.running_time, serial_number=recording.serial_number))

    return await repo.save_recordings(cross_id, runners)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8555,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem"
    )