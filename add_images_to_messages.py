from database.models import Message, Base
from sqlalchemy import Column, String
from database.database import SessionLocal
from database.database import engine
from sqlalchemy.sql import text

session = SessionLocal()
session.execute(text(f"ALTER TABLE \"Messages\" ADD COLUMN image VARCHAR"))
session.commit()
