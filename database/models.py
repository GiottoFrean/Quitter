import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.orm import relationship
from database.database import Base

class Collection(Base):
    __tablename__ = "Collections"
    id = Column(Integer, primary_key=True, index=True)
    messages = relationship('Message', backref='collection', lazy=True)
    round = relationship('Round', backref='collection', lazy=True)

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password_hash = Column(String)

class Message(Base):
    __tablename__ = "Messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    collection_id = Column(Integer, ForeignKey('Collections.id'), index=True)
    user_id = Column(Integer, ForeignKey('Users.id'), index=True)
    posted_time = Column(DateTime)
    censored = Column(Boolean, default=False)

# Association table to represent the many-to-many relationship between Round and Message
round_message_association = Table(
    'RoundMessageAssociation',
    Base.metadata,
    Column('round_id', Integer, ForeignKey('Rounds.id')),
    Column('message_id', Integer, ForeignKey('Messages.id'))
)

class Round(Base):
    __tablename__ = "Rounds"
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('Collections.id'), index=True)
    messages = relationship('Message', secondary=round_message_association)

class Vote(Base):
    __tablename__ = 'Votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    message_id = Column(Integer, ForeignKey('Messages.id'))
    round_id = Column(Integer, ForeignKey('Rounds.id'))
    count = Column(Integer)

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