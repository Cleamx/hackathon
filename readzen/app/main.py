from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.api.endpoints import documents, pages

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="ReadZen API", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(pages.router, tags=["pages"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "readzen"}
