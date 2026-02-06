import os
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .local import db_params_sa

# Prefer DATABASE_URL if provided (e.g., Neon/Supabase), else fallback to local params
db_url = os.environ.get("DATABASE_URL")
if db_url:
	engine = create_engine(db_url)
else:
	engine = create_engine(sqlalchemy.engine.url.URL.create("postgresql", **db_params_sa))

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()