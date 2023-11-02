import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Message(Base):
    __tablename__ = "Messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    collection_id = Column(Integer, ForeignKey('Collections.id'), index=True)