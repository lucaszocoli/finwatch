from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from app.core.database import get_db
from app.core.logging_config import setup_logging, get_logger
from app.routes import users, transactions, fraud_alerts

setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="FinWatch API",
    description="API para cadastro de transações financeiras",
    version="0.1.0",
    docs_url="/docs",
)

logger.info("FinWatch API starting up...")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()

    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'} - "
        f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
    )

    response = await call_next(request)

    process_time = time.time() - start_time

    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Process time: {process_time:.4f}s"
    )

    if response.status_code >= 400:
        logger.warning(
            f"HTTP {response.status_code} - {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'} - "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(fraud_alerts.router, prefix="/api/v1", tags=["fraud-alerts"])

logger.info("API routes registered successfully")


@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "message": "FinWatch - Análise de Transações Financeiras",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        logger.info("Health check - Database connection successful")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed - Database connection error: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
