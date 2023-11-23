import sys
import time
import datetime
import pytz
from sqlalchemy.sql import text
from sqlalchemy import update, desc, func
from database.database import Base, SessionLocal, engine
from database.models import Collection, Message, Round, round_message_association, StateEntry, Vote
import settings
import math

# Function to initialize the database
def setup_database(session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session.add(Collection())
    session.add(StateEntry())
    session.commit()

# Function to start the next collection
def next_collection(session):
    current_collection = session.query(Collection).order_by(Collection.id.desc()).first()
    new_collection = Collection()
    new_round = Round(collection=current_collection, messages=current_collection.messages)
    session.add(new_collection)
    session.add(new_round)
    session.commit()

# Function to progress to the next round
def next_round(session):
    current_round = session.query(Round).order_by(Round.id.desc()).first()
    current_round_count = len(current_round.messages)
    
    # cut the number of messages down by the number each person sees in a round.
    new_round_count = math.ceil(current_round_count / settings.round_comment_pool_size)
    
    # If the new round will be the final one, see if we can add another message to give people some options.
    # Helps to avoid having just 2 messages in the final round.
    if(not new_round_count==1 and new_round_count<settings.round_comment_pool_size):
        removed_messages = current_round_count - new_round_count
        if(removed_messages > 1): # We can add in another message. 
            # Worst case: pool size of 3, 4 messages -> 2 -> 3 in the final round. 
            # If the pool size is weirdly 2, then 3 -> 2 -> 2, which is fine.
            # Sensible case if the round size if 5, then 7 -> 2 -> 3. And 11 -> 3 -> 4. Seems good. 
            new_round_count += 1

    # get top votes messages
    top_voted_messages = session.query(Message).join(Vote).filter(Vote.round_id == current_round.id).group_by(Message.id).order_by(desc(func.sum(Vote.count))).limit(new_round_count).all()
    
    new_round = Round(collection=current_round.collection, messages=top_voted_messages)
    session.add(new_round)
    session.commit()
    return new_round

def get_number_of_rounds_in_collection(number_of_messages, round_comment_pool_size):
    number_of_rounds = 0
    while(number_of_messages > 1):
        number_of_rounds += 1
        number_of_messages = math.ceil(number_of_messages / round_comment_pool_size)
    return number_of_rounds

def update_state(session):
    current_state = session.query(StateEntry).order_by(StateEntry.id.desc()).first()
    current_time = datetime.datetime.now(pytz.utc).replace(tzinfo=None)
    
    new_state = StateEntry()
    make_new_round = False

    if current_state.collection_status == None:
        # transition to collecting
        new_state.collection_id = None
        new_state.collection_status = "collecting"
        new_state.collection_count = None
        new_state.collection_end_time = None
        new_state.collection_round_count = None
    elif current_state.collection_status == "collecting":
        current_collection = session.query(Collection).order_by(Collection.id.desc()).first()
        messages_in_collection = len(current_collection.messages)
        round_is_done = current_state.round_status == None or current_state.round_status == "completed"
        if(messages_in_collection >= settings.minimum_comments_for_collection_to_proceed_to_timing and round_is_done):
            # transition to waiting
            new_state.collection_id = current_collection.id
            new_state.collection_status = "waiting"
            new_state.collection_count = messages_in_collection
            new_state.collection_end_time = current_time + datetime.timedelta(seconds=settings.additional_collection_time)
            new_state.collection_round_count = current_state.collection_round_count
        else:
            # stay in collecting
            new_state.collection_id = current_collection.id
            new_state.collection_status = "collecting"
            new_state.collection_count = messages_in_collection
            new_state.collection_end_time = None
            new_state.collection_round_count = current_state.collection_round_count
    elif current_state.collection_status == "waiting":
        current_collection = session.query(Collection).order_by(Collection.id.desc()).first()
        messages_in_collection = len(current_collection.messages)
        if current_time >= current_state.collection_end_time:
            # transition to new collection
            next_collection(session)
            make_new_round = True
            new_state.collection_id = current_collection.id + 1
            new_state.collection_status = "collecting"
            new_state.collection_end_time = None
            new_state.collection_count = 0
            new_state.collection_round_count = get_number_of_rounds_in_collection(messages_in_collection, settings.round_comment_pool_size)
        else:
            # stay in waiting
            new_state.collection_id = current_collection.id
            new_state.collection_status = "waiting"
            new_state.collection_end_time = current_state.collection_end_time
            new_state.collection_count = messages_in_collection
            new_state.collection_round_count = current_state.collection_round_count
    else:
        raise Exception("Invalid collection status: " + current_state.collection_status)

    if current_state.round_status == None or make_new_round:
        round = session.query(Round).order_by(Round.id.desc()).first()
        if round is not None:
            # transition to collecting votes
            new_state.round_status = "collecting"
            new_state.round_voters = 0
            new_state.round_end_time = None
            new_state.round_id = round.id
            new_state.round_number = 1
        else:
            # stay in None obviously
            current_state.round_status = None
    elif current_state.round_status == "collecting":
        round = session.query(Round).order_by(Round.id.desc()).first()
        # Count the PEOPLE who voted. 
        # Each time somone hits "send-votes" the total views are incremented by min(round_comment_pool_size, number of messages in the round).
        round_voters = session.query(func.count(Vote.user_id)).filter(Vote.round_id == round.id).scalar() / min(settings.round_comment_pool_size, len(round.messages))
        if round_voters is None: round_voters = 0
        if round_voters >= settings.minimum_voters_for_round_to_proceed_to_timing:
            # transition to waiting
            new_state.round_status = "waiting"
            new_state.round_voters = round_voters
            new_state.round_end_time = current_time + datetime.timedelta(seconds=int(settings.voting_time_all_rounds / max(current_state.collection_round_count,1)))
            new_state.round_id = round.id
            new_state.round_number = current_state.round_number
        else:
            # stay in collecting
            new_state.round_status = "collecting"
            new_state.round_voters = round_voters
            new_state.round_end_time = None
            new_state.round_id = round.id
            new_state.round_number = current_state.round_number
    elif current_state.round_status == "waiting":
        if current_time >= current_state.round_end_time:
            # transition to new round
            new_round = next_round(session)
            new_round_message_count = len(new_round.messages)
            if(new_round_message_count == 1):
                # done, there is a winner
                new_state.round_status = "completed"
                new_state.round_end_time = None
                new_state.round_voters = None
                new_state.round_id = None
                new_state.round_number = current_state.round_number + 1
            else:
                # continue
                new_state.round_status = "collecting"
                new_state.round_end_time = None
                new_state.round_voters = 0
                new_state.round_id = new_round.id
                new_state.round_number = current_state.round_number + 1
        else:
            # stay in waiting
            round = session.query(Round).order_by(Round.id.desc()).first()
            round_voters = session.query(func.count(Vote.user_id)).filter(Vote.round_id == round.id).scalar() / min(settings.round_comment_pool_size, len(round.messages))
            new_state.round_status = "waiting"
            new_state.round_end_time = current_state.round_end_time
            new_state.round_voters = round_voters
            new_state.round_id = current_state.round_id
            new_state.round_number = current_state.round_number
    elif current_state.round_status == "completed":
        new_state.round_status = "completed"
        new_state.round_end_time = None
        new_state.round_voters = None
        new_state.round_id = None
        new_state.round_number = None
    else:
        raise Exception("Invalid round status: " + current_state.round_status)
    
    state_str = str(new_state.collection_id) + " " + new_state.collection_status + " " + str(new_state.collection_count) + " " + str(new_state.collection_end_time) + " Round: " + str(new_state.round_id) + " " + str(new_state.round_status) + " " + str(new_state.round_voters) + " " + str(new_state.round_end_time)
    print("Updating", time.time(), state_str)
    session.add(new_state)
    session.commit()

if __name__ == "__main__":
    if("reset" in sys.argv):
        setup_database(SessionLocal())

    while True:
        session = SessionLocal()
        update_state(session)
        session.close()
        time.sleep(1) # just so the database isn't always being accessed.