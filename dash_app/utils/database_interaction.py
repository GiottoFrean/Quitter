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

def add_comment(message_content, user_id):
    session = SessionLocal()
    latest_collection = session.query(Collection).order_by(Collection.id.desc()).first()
    if latest_collection:
        session.add(Message(content=message_content,collection=latest_collection, user_id=user_id, posted_time=datetime.datetime.now(pytz.utc).replace(tzinfo=None)))
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

def add_votes_to_message(round_id,message_id,votes_to_add,user_id):
    session = SessionLocal()
    # add a votes object
    votes = Vote(round_id=round_id,message_id=message_id,user_id=user_id, count=votes_to_add)
    session.add(votes)
    session.commit()

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
        avg_votes.append(session.query(func.avg(Vote.count)).filter(Vote.message_id == message_id, Vote.round_id == round_id).scalar())
    session.close()
    return avg_votes

def get_current_state():
    session = SessionLocal()
    current_state = session.query(StateEntry).order_by(StateEntry.id.desc()).first()
    session.close()
    return current_state

def get_total_comments_sent(user_id,collection_id):
    session = SessionLocal()
    total_comments_sent = session.query(func.count(Message.id)).filter(Message.user_id == user_id, Message.collection_id == collection_id).scalar()
    session.close()
    return total_comments_sent if total_comments_sent else 0

def has_user_voted_in_round(user_id,round_id):
    session = SessionLocal()
    has_voted = session.query(Vote).filter(Vote.user_id == user_id, Vote.round_id == round_id).first()
    session.close()
    return has_voted is not None

def get_user(username):
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def get_username_from_id(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user.username

def check_user_id_exists(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username,password):
    session = SessionLocal()
    session.add(User(username=username,password_hash=hash_password(password)))
    session.commit()
    session.close()

def get_messages_for_user(user_name,count,offset):
    session = SessionLocal()
    user = session.query(User).filter(User.username == user_name).first()
    # fetch top messages for user
    messages = []
    if user:
        messages = session.query(Message).filter(Message.user_id == user.id).order_by(Message.id.desc()).offset(offset).limit(count).all()
    session.close()
    return messages

def fetch_message_sender_name(message_id):
    session = SessionLocal()
    message = session.query(Message).filter(Message.id == message_id).first()
    sender_name = ""
    if message:
        sender_name = session.query(User).filter(User.id == message.user_id).first().username
    session.close()
    return sender_name

def get_highest_round_for_message(message):
    session = SessionLocal()
    message_collection_id = message.collection_id
    stmt = (
        select(func.count(round_message_association.c.message_id).label('count'))
        .select_from(round_message_association)
        .join(Round, round_message_association.c.round_id == Round.id)
        .where(
            and_(
                Round.collection_id == message_collection_id,
                round_message_association.c.message_id == message.id
            )
        )
    )
    result = session.execute(stmt).fetchone()
    in_round_count = result[0]
    total_round_count = (
        session.query(func.count(Round.id))
        .filter(Round.collection_id == message_collection_id)
        .scalar()
    )
    session.close()
    return in_round_count, total_round_count
    

def get_messages(lower=0, count=10):
    session = SessionLocal()
    messages = session.query(Message).order_by(Message.id.desc()).offset(lower).limit(count).all()
    session.close()
    content = [m.content for m in messages]
    ids = [m.id for m in messages]
    for i in range(len(ids)):
        print(ids[i],content[i])


def get_users(lower=0, count=10):
    session = SessionLocal()
    users = session.query(User).order_by(User.id.desc()).offset(lower).limit(count).all()
    session.close()
    content = [u.username for u in users]
    ids = [u.id for u in users]
    for i in range(len(ids)):
        print(ids[i],content[i])

def get_round_messages(round_id):
    session = SessionLocal()
    round_messages = session.query(round_message_association).filter(round_message_association.c.round_id == round_id).all()
    session.close()
    for round_message in round_messages:
        print(round_message.content)