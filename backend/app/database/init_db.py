"""
Database initialization script.
"""
import logging
from sqlalchemy import create_engine
from ..models.database_models import Base
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables."""
    try:
        # Create engine
        engine = create_engine(settings.database_url, echo=True)
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()
