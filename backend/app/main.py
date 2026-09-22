from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import APP_NAME, VERSION, API_PREFIX
from app.database import init_db
from app.routers import (
    auth,
    catalog,
    inventory,
    tables,
    transactions,
    shifts,
    finance,
    promo,
    reports,
    integrations,
    sync,
    settings,
    attendance
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on startup
    init_db()
    yield

app = FastAPI(
    title=APP_NAME,
    description="Synchronized Backend API and Relational Database for Aurora Cafe POS, integrating all 41 modules.",
    version=VERSION,
    lifespan=lifespan
)

# Enable CORS for frontend POS / Mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All Routers under API_PREFIX
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(inventory.router, prefix=API_PREFIX)
app.include_router(tables.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(shifts.router, prefix=API_PREFIX)
app.include_router(finance.router, prefix=API_PREFIX)
app.include_router(promo.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(integrations.router, prefix=API_PREFIX)
app.include_router(sync.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(attendance.router, prefix=API_PREFIX)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Mount Static Files
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file))

@app.get("/pos")
def serve_pos():
    pos_file = STATIC_DIR / "pos.html"
    return FileResponse(str(pos_file))

@app.get("/api/health")
def root():
    return {
        "status": "online",
        "app": APP_NAME,
        "version": VERSION,
        "docs_url": "/docs",
        "modules_covered": 41
    }
