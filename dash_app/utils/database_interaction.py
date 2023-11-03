import sys
from models import Collection, Message, Round, round_message_votes_association, StateEntry
from database import Base, SessionLocal, engine
from sqlalchemy.sql import text
from sqlalchemy import update
import numpy as np
from sqlalchemy import desc, func
import time
import settings
from sqlalchemy import cast, Float

def add_comment(message_content):
    session = SessionLocal()
    latest_collection = session.query(Collection).order_by(Collection.id.desc()).first()
    if latest_collection:
        session.add(Message(content=message_content,collection=latest_collection))
        session.commit()
    session.close()

def fetch_messages_in_round():
    session = SessionLocal()
    current_round = session.query(Round).order_by(Round.id.desc()).first()
    selected_messages = []
    if current_round:
        messages = current_round.messages
        number_of_messages_in_round = len(messages)
        if number_of_messages_in_round > settings.round_comment_pool_size:
            random_indices = np.random.choice(number_of_messages_in_round, settings.round_comment_pool_size, replace=False)
            selected_messages = [messages[i] for i in random_indices]
        else:
            selected_messages = messages
    session.close()
    return selected_messages

def add_votes_to_message(round_id,message_id,votes_to_add):
    session = SessionLocal()
    round_message_row = session.query(round_message_votes_association).filter(
        round_message_votes_association.c.round_id == round_id).filter(
        round_message_votes_association.c.message_id == message_id).first()
    
    if round_message_row:
        session.execute(update(round_message_votes_association).where(
            round_message_votes_association.c.round_id == round_id).where(
            round_message_votes_association.c.message_id == message_id).values(votes=round_message_row.votes + votes_to_add, views=round_message_row.views + 1))
    session.commit()
    session.close()

def get_current_state():
    session = SessionLocal()
    current_state = session.query(StateEntry).order_by(StateEntry.id.desc()).first()
    session.close()
    return current_state

def fetch_top_messages(count=10,offset=0):
    session = SessionLocal()
    top_messages = []
    # go through rounds, get the message if the round has a single message. Ignore the first collection, as it is the one running now.
    # If a collection has been won, it means a new collection has been started. So offset by 1.
    for collection in session.query(Collection).order_by(Collection.id.desc()).offset(1+offset).limit(count).all():
        last_round = session.query(Round).filter(Round.collection_id == collection.id).order_by(Round.id.desc()).first()
        if last_round:
            if len(last_round.messages) == 1:
                top_messages.append(last_round.messages[0])
    session.close()
    return top_messages

def get_the_average_votes_for_messages_in_round(message_ids,round_id):
    session = SessionLocal()
    avg_votes = []
    for message_id in message_ids:
        round_message_row = session.query(round_message_votes_association).filter(
            round_message_votes_association.c.round_id == round_id).filter(
            round_message_votes_association.c.message_id == message_id).first()
        if round_message_row:
            avg_votes.append(round_message_row.votes / max(round_message_row.views,1))
        else:
            avg_votes.append(0)
    session.close()
    return avg_votes