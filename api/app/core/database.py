from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("database")

logger.info("Initializing database engine")
engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=300, echo=settings.debug
)
logger.info("Database engine initialized successfully")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        logger.debug("Database session closed")
        db.close()
