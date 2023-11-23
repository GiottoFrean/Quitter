import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .local import db_params_sa

engine = create_engine(sqlalchemy.engine.url.URL.create("postgresql", **db_params_sa))
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()