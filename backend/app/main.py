from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contacts import router as contacts_router
from app.api.dashboard import router as dashboard_router
from app.api.interactions import router as interactions_router
from app.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Smart Follow-Up Reminder", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(contacts_router, prefix="/api/v1")
app.include_router(interactions_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
