import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base

class StateEntry(Base):
    __tablename__ = 'StateEntries'
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('Collections.id'))
    collection_status = Column(String)
    collection_count = Column(Integer)
    collection_end_time = Column(DateTime)
    collection_round_count = Column(Integer)
    round_id = Column(Integer, ForeignKey('Rounds.id'))
    round_status = Column(String)
    round_voters = Column(Integer)
    round_end_time = Column(DateTime)
    round_number = Column(Integer)