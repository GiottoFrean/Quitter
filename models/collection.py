import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Collection(Base):
    __tablename__ = "Collections"
    id = Column(Integer, primary_key=True, index=True)
    messages = relationship('Message', backref='collection', lazy=True)
    round = relationship('Round', backref='collection', lazy=True)