import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from database import Base

# Association table to represent the many-to-many relationship between Round and Message
round_message_votes_association = Table(
    'RoundMessageAssociation',
    Base.metadata,
    Column('round_id', Integer, ForeignKey('Rounds.id')),
    Column('message_id', Integer, ForeignKey('Messages.id')),
    Column('votes', Integer, default=0),
    Column('views', Integer, default=0)
)

class Round(Base):
    __tablename__ = "Rounds"
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('Collections.id'), index=True)
    messages = relationship('Message', secondary=round_message_votes_association)
