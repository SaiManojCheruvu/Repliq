from dotenv import load_dotenv
load_dotenv()

from database import engine, Base
import models
from logger import get_logger
logger = get_logger("repliq.auth")
import sys



def create_tables():
    logger.info("Connecting to database...")
    try:
        Base.metadata.create_all(bind=engine)
        tables = list(Base.metadata.tables.keys())
        logger.info("Tables created successfully (%d total):", len(tables))
        for table in tables:
            logger.info("- %s", table)
    except Exception as e:
        logger.error("Error creating tables: %s", e)
        sys.exit(1)


def drop_tables():
    logger.warning("Dropping all tables -- this will delete all data and is irreversible!")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully.")
    except Exception as e:
        logger.error("Error dropping tables: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    if  len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_tables()
    else:
        create_tables()
    