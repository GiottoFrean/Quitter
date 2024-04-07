import sys
from database.models import Collection, Message, Round, round_message_association, StateEntry, User, Vote
from database.database import Base, SessionLocal, engine
from sqlalchemy.sql import text
import numpy as np
from sqlalchemy import desc, func, select, update, and_
import time
import settings
from sqlalchemy import cast, Float
import hashlib
import datetime
import pytz

# add a column to the messages table, called "previous_message_id"

session = SessionLocal()
session.execute(text('ALTER TABLE "Messages" ADD COLUMN previous_message_id INTEGER'))
session.commit()