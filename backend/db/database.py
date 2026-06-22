from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from core.config import settings

import os
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        clean_path = db_path
        if clean_path.startswith("./"):
            clean_path = clean_path[2:]
        elif clean_path.startswith(".\\"):
            clean_path = clean_path[2:]
        abs_db_path = os.path.abspath(os.path.join(backend_dir, clean_path))
        db_url = f"sqlite:///{abs_db_path}"

engine = create_engine(
    db_url
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)        