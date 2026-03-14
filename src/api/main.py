"""FastAPI 应用入口"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import documents, tasks, reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TenderIntegrity API",
    description="标书雷同与语义查重 — 医疗采购监管前置风险筛查工具",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    from src.storage.database import init_db
    await init_db()
    logger.info("TenderIntegrity API 启动完成")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "TenderIntegrity"}
