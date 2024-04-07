import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash_app.utils import database_interaction
import dash_bootstrap_components as dbc
import settings
import dash_mantine_components as dmc
import numpy as np
import datetime
import pytz
import dash_extensions
import json
import requests
import math
import os

app_config = json.load(open("dash_app/app_config.json"))

dash.register_page(__name__,path="/", title="Quitter")

# voting row is a row with a message, a voting square, and up/down vote buttons
def make_voting_row(index):
    old_message = html.Div(
        [
            html.Div(id={"type":"old-message-image","index":index}, className="voting-image-container"),
            html.Div(id={"type":"old-message-text","index":index}, className="message-text-old")
        ],
        className="voting-row-old-message-container"
    )
    current_message = html.Div(
        [
            html.Div(id={"type":"message-image","index":index}, className="voting-image-container"),
            html.Div(id={"type":"message-text","index":index}, className="message-text")
        ],
        className="voting-row-current-message-container"
    )
    message_container = dbc.Button(
        [
            old_message,
            current_message
        ],
        id={"type":"voting-message-container","index":index},
        className="voting-message-container", 
        n_clicks=0, 
        color="none"
    )
    down_vote = dbc.Button(children=[html.I(className="fas fa-thumbs-down")],id={"type":"downvote-button","index":index}, className='vote-button-down',n_clicks=0,color="none")
    vote_square = html.Div(
        html.Div(className='vote-square', id={"type":"vote-square","index":index}, children=[
            html.Div(id={"type":"vote-square-marker","index":index},className="vote-square-marker"),
            html.Div(
                html.Table(className="grid-table", children=[
                    html.Tbody(
                        html.Tr(className="grid-table-row", children=[
                            html.Td(className="grid-table-cell") for c in range(10)
                        ])
                    ) for r in range(10)
                ]),
                className="vote-square-grid-container"
            ),
            html.Div(html.Div(id={"type":"vote-square-number","index":index}, className="vote-square-number"), className="vote-square-number-holder")
        ]),
        className="vote-square-container"
    )
    up_vote = dbc.Button(children=[html.I(className="fas fa-thumbs-up")],id={"type":"upvote-button","index":index}, className='vote-button-up',n_clicks=0,color="none")
    up_clicks_store = dcc.Store(id={"type":"up-nclick-store","index":index}, data=0)
    down_clicks_store = dcc.Store(id={"type":"down-nclick-store","index":index}, data=0)
    id_store = dcc.Store(id={"type":"store-vote-round-id","index":index}, data=-1)
    id_store_old = dcc.Store(id={"type":"store-vote-round-id-old","index":index}, data=-1)
    votes_store = dcc.Store(id={"type":"votes-store","index":index}, data=0)
    store_last_round_votes = dcc.Store(id={"type":"store-last-votes","index":index}, data=0)
    store_old_last_round_votes = dcc.Store(id={"type":"store-last-votes-old","index":index}, data=0)
    
    vote_buttons = html.Div(
        children=[
            up_vote,
            down_vote,
            id_store,
            id_store_old,
            up_clicks_store,
            down_clicks_store,
            votes_store,
            store_last_round_votes,
            store_old_last_round_votes
        ],
        className="voting-row-buttons"
    )
    
    return html.Div(
        children=[
            message_container,
            html.Div(
                [
                    vote_square,
                    vote_buttons
                ],
                className="voting-row-square-and-buttons"
            )
        ],
        id={"type":"voting-row","index":index},
        className="voting-row hide"
    )

def make_credit_row(index):
    return html.Div(className="credit-row", children=[
        html.Div(id={"type":"credit-marker","index":index}, className="credit-marker"),
        html.Div(
            html.Table(className="grid-table", children=[
                html.Tbody(
                    [html.Tr(className="grid-table-row", children=[
                        html.Td(className="grid-table-column", children=[
                            html.Div(className="grid-table-cell")
                        ]) for c in range(20)
                    ])]
                )
            ]),
            className="credit-grid-container"
        )
    ])

application_status_layout = html.Div(
    className="application-status-container",
    id="application-status-container",
    children=[
        html.Div(html.Div("Status:",className="application-status-text"),id="application-status")
    ]
)

credit_and_voting_layout = html.Div(
    [
        html.Div([make_voting_row(index) for index in range(settings.round_comment_pool_size)], className="voting-container"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(html.Div([make_credit_row(index) for index in range(settings.round_comment_pool_size)]), className="credits-container"),
                        dbc.Button("Send votes", id="send-votes-button", className="send-votes-button", n_clicks=0, color="none"),
                        dcc.Store(id="send-votes", data=None),
                        dcc.Store(id="recaptcha-send-votes", data=None),
                        html.Div(id="send-votes-output")
                    ],
                    className="credits-and-vote-container"
                )
            ],
            className = "credits-and-vote-show-hide-wrapper hide",
            id="credits-and-vote-show-hide-wrapper"
        )
    ],
    className="credit-and-voting-container",
    id="credit-and-voting-container"
)

previous_messages_layout = html.Div(
    id="previous-messages-container",
    className="previous-messages-container",
    children=[
        html.Div("Previous messages", className="previous-messages-title"),
        html.Div(id="hidden-div-reply-focus", style={"display":"none"}),
        html.Div([dbc.Button("Show older", id="show-more-button", className="show-more-button", n_clicks=0, color="none")],className="show-more-button-container"),
        html.Div(
            id="previous-messages",
            children = [],
            className="previous-messages"
        ),
        dcc.Store(id="previous-messages-ids", data=[]),
        dcc.Store(id="all-loaded-previous-message-ids", data=[]),
        dcc.Store(id="previous-message-ids-ruled-out", data=[])
    ]
)

input_message_layout = html.Div(
    className='fixed-input-area', 
    children=[
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            id="input-in-reply-message",
                            className="input-in-reply-message"
                        ),
                        html.Div(
                            dbc.Button(
                                children=[html.I(className="fas fa-times")],
                                id='cancel-reply-button', 
                                className='cancel-reply-button',
                                n_clicks=0,
                                color="none",
                            ),
                            className='cancel-reply-button-container'
                        ),
                        dcc.Store(id="reply-message-id", data="NA")
                    ],
                    id="input-in-reply-message-container",
                    className="input-in-reply-message-container",
                    style={"display":"none"}
                ),
                html.Div(
                    children=[
                        dcc.Store(id="message-data-store", data=None),
                        html.Div(id="message-sent-trigger", style={"display":"none"}),
                        dash_extensions.EventListener(
                            dmc.Textarea(id='message-input', placeholder='Type your message...', className='message-input', size="lg", maxRows=10, autosize=True),
                            id="message-input-listener",
                            className="message-input-listener",
                            events=[{"event": "keydown", "props": ["key", "shiftKey"]}],
                        ),
                        html.Div(id="hidden-div-check-loaded", style={"display": "none"}),
                        dcc.Store(id="send-clicks", data=0),
                        html.Div(
                            dbc.Button(
                                children=[
                                    html.I(className="fas fa-paper-plane")
                                ],
                                id='send-button', 
                                className='message-send-button',
                                n_clicks=0,
                                color="none",
                            ),
                            className='message-send-button-container'
                        ),
                        dcc.Store(id="image-select-store", data=None),
                        html.Div(
                            dbc.Button(
                                children=[
                                    html.I(className="fas fa-paperclip", id="image-button-logo")
                                ],
                                id='image-button', 
                                className='image-open-button',
                                n_clicks=0,
                                color="none",
                            ),
                            className='image-open-button-container'
                        ),
                        dcc.Store(id="total-sent-messages", data={"collection_id":-1,"total":0}) # record the total number of messages sent.
                    ],
                    className="message-input-and-button"
                )
            ],
            className="message-input-and-previous-message"
        )
    ]
)

show_more_modal = dbc.Modal(
    [
        dbc.ModalHeader([dbc.Button("Load older", id="show-more-modal-load-older", className="show-more-button-on-modal", n_clicks=0, color="none")]),
        dcc.Store(id="show-more-current-oldest-message-index"),
        dbc.ModalBody([], id="show-more-modal-body", className="show-more-modal-body"),
    ],
    id="show-more-modal",
    is_open=False
)

def make_image_button_and_container(index):
    return dcc.Loading(
        dbc.Button(
            id={"type":"image-select-modal-image","index":index},
            className="image-select-modal-image-button",
            n_clicks=0,
            color="none"
        ),
        type="circle",
        color="red",
        fullscreen=False,
        style={"width": "50px", "height": "50px"}
    )

image_files = ["/assets/images/"+file for file in os.listdir("dash_app/static/images") if file.endswith(".jpg") or file.endswith(".png")]
image_page_size = 10
number_of_pages = math.ceil(len(image_files)/image_page_size)
image_select_modal = dbc.Modal(
    [
        dbc.ModalHeader("Select an image"),
        dbc.Pagination(max_value=number_of_pages, fully_expanded=False, id="image-select-modal-pagination", className="image-select-modal-pagination"),
        dbc.ModalBody([make_image_button_and_container(index) for index in range(image_page_size)], className="image-select-modal-body"),
    ],
    id="image-select-modal",
    is_open=False
)

refresh_component = dcc.Interval(id='home-refresh-interval', interval=5000, n_intervals=0)
store_round_state = dcc.Store(id='store-round-state', data={"round_id":-1,"collection_id":-1,"message_ids":[],"messages":[], "images":[]})
round_state_switch_time = dcc.Store(id='round-state-switch-time', data=None)


layout = html.Div(
    [
        application_status_layout,
        image_select_modal,
        credit_and_voting_layout,
        previous_messages_layout,
        input_message_layout,
        refresh_component,
        store_round_state,
        show_more_modal,
        round_state_switch_time
    ]
)

@dash.callback(
    Output({"type":"image-select-modal-image","index":dash.ALL}, "children"),
    [Input("image-select-modal-pagination", "active_page")]
)
def update_image_select_modal_images(page):
    if page is None:
        page = 0
    else:
        page = page - 1
    relevant_files = image_files[page*image_page_size:(page+1)*image_page_size]
    filenames_small = [f.replace("/assets/images/","/assets/images_small/") for f in relevant_files]
    filenames_final = [filenames_small[i] if os.path.exists(filenames_small[i]) else relevant_files[i] for i in range(len(relevant_files))]
    return [html.Div(html.Img(src=f, className="image"), className="image-container") for f in filenames_final]+[None for i in range(image_page_size-len(relevant_files))]


#show the images when the paperclip is clicked, and hide them when an image is slected.
@dash.callback(
    Output("image-select-store", "data"),
    Output("image-select-modal", "is_open"),
    Output("image-button-logo", "className"),
    [Input("image-button", "n_clicks"), Input({"type":"image-select-modal-image","index":dash.ALL}, "n_clicks"), Input("image-select-store", "data"), Input("message-data-store", "data")],
    [State("image-select-modal", "is_open"), State({"type":"image-select-modal-image","index":dash.ALL}, "n_clicks"), State("image-select-modal-pagination", "active_page")],
)
def select_image(image_button_clicks, image_clicks, current_image, message_data, is_open, image_clicks_old, page):
    ctx = dash.callback_context
    if ctx.triggered_id == "image-button":
        if not current_image is None:
            # cancel the image selection, don't open the modal.
            return None, False, "fas fa-paperclip"
        else:
            return None, True, "fas fa-paperclip"
    else:
        if ctx.triggered_id is None:
            raise dash.exceptions.PreventUpdate
        if ctx.triggered_id == "message-data-store":
            return None, False, "fas fa-paperclip"

        index = ctx.triggered_id["index"]
        if page is None:
            page = 0
        else:
            page = page - 1
        filename = image_files[page*image_page_size+index]
        return filename, False, "fas fa-times"


# prevent the enter key from adding a new line, unless pressed with shift. 
dash.clientside_callback(
    """
    function(dummy) {
        var messageInput = document.querySelector('#message-input');
        if (messageInput) {
            messageInput.addEventListener('keydown', function (e) {
                if (e.keyCode === 13 && !e.shiftKey && window.innerWidth > 700) {
                    e.preventDefault();
                }
            });
        } else {
            console.log("message-input not found");
        }
      }
    """,
    Output('hidden-div-check-loaded', 'children'),
    Input('hidden-div-check-loaded', 'children')
)

# update the message data store when the send button is clicked, or when enter is pressed
dash.clientside_callback(
    """
    function(n_events, send_clicks, enterEvent, text, reply_id, send_clicks_store) {
        if (enterEvent && enterEvent.key === "Enter" && !enterEvent.shiftKey && window.innerWidth > 700) { // enter key pressed & not on a phone
            return [{"message": text, "reply_id": reply_id}, send_clicks];
        } else if (send_clicks > send_clicks_store) {
            return [{"message": text, "reply_id": reply_id}, send_clicks];
        } else {
            return [window.dash_clientside.no_update, send_clicks];
        }
    }
    """,
    Output("message-data-store", "data"),
    Output("send-clicks", "data"),
    Input("message-input-listener", "n_events"),
    Input("send-button", "n_clicks"),
    State("message-input-listener", "event"),
    State("message-input", "value"),
    State("reply-message-id", "data"),
    State("send-clicks", "data")
)

@dash.callback(
    Output("send-button", "disabled"),
    [Input("login", "data")],
)
def disable_send_button(login):
    if login is None:
        return True
    else:
        return False

# process a new message, and get ready to send if it looks alright and the user hasn't sent too many messages.
@dash.callback(
    Output('message-input', 'error'),
    Output('message-input', 'value'),
    Output('message-sent-trigger', 'children'),
    [Input('message-data-store', 'data')],
    [State('login', 'data'), State('store-round-state', 'data'), State('image-select-store', 'data')]
)
def send_message(message_data, login, round_state, image):
    if(not (message_data is None and image is None)):
        message = message_data["message"]
        reply_id = message_data["reply_id"]
        if reply_id=="NA":
            reply_id = None
        lines = message.split('\n')
        if len(message) > settings.max_characters:
            return "Error: message has too many characters. Please keep it to "+str(settings.max_characters)+" at most.", dash.no_update, dash.no_update
        else:
            if(len(message) > 0 or not image is None):
                if login is None:
                    return "Error: you are not logged in.", dash.no_update, dash.no_update
                
                total_sent_so_far = database_interaction.get_total_comments_sent(login["user_id"], round_state["collection_id"])
                if total_sent_so_far >= settings.max_messages_per_collection:
                    return "Error: you have already sent "+str(settings.max_messages_per_collection)+" messages. Please wait for the next round.", dash.no_update, dash.no_update
                
                if not database_interaction.check_user_id_exists(login["user_id"]):
                    return "Error: you are not logged in.", dash.no_update, dash.no_update

                database_interaction.add_comment(message, login["user_id"], image, reply_id)
                return "", "", ""
    
    raise dash.exceptions.PreventUpdate

# update the application status (stuff at the top of the page)
@dash.callback(
    Output('application-status', 'children'),
    [Input('home-refresh-interval', 'n_intervals')],
    [State('round-state-switch-time', 'data')]
)
def update_application_status(n_intervals, switch_time):
    state = database_interaction.get_current_state()
    if(not switch_time is None):
        return html.Div("Round complete, displaying results", className="application-status-text")
    else:
        id = state.id
        collection_id = state.collection_id
        collection_status = state.collection_status
        collection_count = state.collection_count
        collection_end_time = state.collection_end_time
        collection_round_count = state.collection_round_count
        round_id = state.round_id
        round_status = state.round_status
        round_voters = state.round_voters
        round_end_time = state.round_end_time
        round_number = state.round_number

        if round_status == "collecting":
            if(round_number is None or collection_round_count is None):
                return html.Div("Loading....", className="application-status-text")
            else:
                return html.Div(f"Status: Round {round_number} / {collection_round_count} is being run. Waiting for minimum voters ({round_voters} / {settings.minimum_voters_for_round_to_proceed_to_timing}).", className="application-status-text")
        elif round_status == "waiting":
            if(round_end_time is None or round_number is None or collection_round_count is None or round_voters is None):
                return html.Div("Loading....", className="application-status-text")
            else:
                time_remaining = round_end_time - datetime.datetime.now(pytz.utc).replace(tzinfo=None)
                time_remaining_total_seconds = max(0,int(round(time_remaining.total_seconds(), 0)))
                time_remaining_minutes = round(time_remaining_total_seconds/60, 2)
                return html.Div(f"Status: Round {round_number} / {collection_round_count} is being run. {round_voters} people have voted so far with {time_remaining_minutes} minutes remaining.", className="application-status-text")
        else:
            if collection_status == "collecting":
                if(collection_count is None):
                    return html.Div("Loading....", className="application-status-text")
                else:
                    return html.Div(f"Status: Collecting a minimum number of comments ({collection_count} / {settings.minimum_comments_for_collection_to_proceed_to_timing}).", className="application-status-text")
            elif collection_status == "waiting":
                if(collection_end_time is None or collection_count is None):
                    return html.Div("Loading....", className="application-status-text")
                else:
                    time_remaining = collection_end_time - datetime.datetime.now(pytz.utc).replace(tzinfo=None)
                    time_remaining_total_seconds = max(0,int(round(time_remaining.total_seconds(), 0)))
                    time_remaining_minutes = round(time_remaining_total_seconds/60, 2)
                    return html.Div(f"Status: Collecting additional comments. Current total is {collection_count}. {time_remaining_minutes} minutes remaining.", className="application-status-text")

# set the next round state (if there is a new round) and save the old votes for displaying. 
# when a new round is available, set the timer and update 'old votes' for display.
# then when the timer is out, switch the round. 
@dash.callback(
    Output('store-round-state', 'data'),
    Output({'type': 'store-vote-round-id', 'index': dash.ALL}, 'data'),
    Output({'type': 'store-last-votes', 'index': dash.ALL}, 'data'),
    Output('round-state-switch-time', 'data'),
    [Input('home-refresh-interval', 'n_intervals')],
    [State('store-round-state', 'data'), State('round-state-switch-time', 'data')]
)
def update_round_state(n_intervals, current_state, switch_time):
    database_state = database_interaction.get_current_state()
    if(not database_state is None):
        if(database_state.round_id != current_state["round_id"]):
            # the round has changed.
            current_time = datetime.datetime.now(pytz.utc).replace(tzinfo=None)
            action = "nothing"
            if(switch_time is None):
                if (len(current_state["messages"]) > 1):
                    action = "set timer, get old votes"
                else:
                    action = "set new round"
            else:
                if(current_time >= datetime.datetime.fromisoformat(switch_time)):
                    action = "set new round"
                else:
                    action = "nothing"
            if(action=="set timer, get old votes"):
                old_votes = database_interaction.get_the_average_votes_for_messages_in_round(current_state["message_ids"], current_state["round_id"])
                old_votes = [round(v,1) for v in old_votes]
                old_votes = old_votes + [0 for i in range(settings.round_comment_pool_size - len(old_votes))]
                return dash.no_update, [dash.no_update for i in range(settings.round_comment_pool_size)], old_votes, current_time + datetime.timedelta(seconds=settings.time_to_show_results)
            elif(action=="set new round"):
                new_state = {}
                new_state["round_id"] = database_state.round_id
                new_state["collection_id"] = database_state.collection_id
                messages = database_interaction.fetch_messages_in_round()
                if(len(messages) == 0):
                    new_state["message_ids"] = []
                    new_state["previous_message_ids"] = []
                    new_state["messages"] = []
                    new_state["previous_messages"] = []
                    new_state["images"] = []
                    new_state["previous_images"] = []
                else:   
                    previous_messages = [database_interaction.get_message_by_id(m.previous_message_id) if not m.previous_message_id is None else None for m in messages]
                    new_state["message_ids"] = [m.id for m in messages]
                    new_state["previous_message_ids"] = [m.previous_message_id for m in messages]
                    new_state["messages"] = [m.content if not m.censored else "CENSORED" for m in messages]
                    new_state["previous_messages"] = [m.content if m and not m.censored else ("CENSORED" if m else None) for m in previous_messages]
                    new_state["images"] = [m.image if not m.censored else None for m in messages]
                    new_state["previous_images"] = [m.image if m and not m.censored else None for m in previous_messages]
                return new_state, [database_state.round_id for i in range(settings.round_comment_pool_size)], [dash.no_update for i in range(settings.round_comment_pool_size)], None
    raise dash.exceptions.PreventUpdate

# sets the display of the voting messages (whether to show them, etc)
@dash.callback(
    Output({"type":"message-text","index":dash.ALL}, "children"),
    Output({"type":"message-image","index":dash.ALL}, "children"),
    Output({"type":"old-message-text","index":dash.ALL}, "children"),
    Output({"type":"old-message-image","index":dash.ALL}, "children"),
    Output({"type":"voting-row","index":dash.ALL}, "className"),
    Output("credits-and-vote-show-hide-wrapper", "className"),
    [Input("store-round-state", "data")],
)
def update_voting_stuff(state):
    messages = state["messages"]
    previous_message_ids = state["previous_message_ids"]
    if(len(messages) <= 1):
        # round is done, only 1 message left. 
        content = ["" for m in range(settings.round_comment_pool_size)]
        images = [None for m in range(settings.round_comment_pool_size)]
        old_content = ["" for m in range(settings.round_comment_pool_size)]
        old_images = [None for m in range(settings.round_comment_pool_size)]
        rows_classnames = ["voting-row hide" for m in range(settings.round_comment_pool_size)]
        credit_and_voting_classname = "credits-and-vote-show-hide-wrapper hide"
    else:
        content = [messages[m] if m < len(messages) else "" for m in range(settings.round_comment_pool_size)]
        old_content = [state["previous_messages"][m] if m < len(messages) else "" for m in range(settings.round_comment_pool_size)]
        images = [html.Div(html.Img(src=state["images"][m], className="image"), className="image-container") if m < len(messages) and not state["images"][m] is None else None for m in range(settings.round_comment_pool_size)]
        old_images = [html.Div(html.Img(src=state["previous_images"][m], className="image-small"), className="image-container") if m < len(messages) and not state["previous_images"][m] is None else None for m in range(settings.round_comment_pool_size)]
        rows_classnames = ["voting-row show" if m<len(messages) else "voting-row hide" for m in range(settings.round_comment_pool_size)]
        credit_and_voting_classname = "credits-and-vote-show-hide-wrapper show"
    return content, images, old_content, old_images, rows_classnames, credit_and_voting_classname


dash.clientside_callback(
    """
    function(upvote_nclicks, downvote_nclicks, round_id, last_votes, all_votes, clicked_votes, up_clicks_old, down_clicks_old, round_id_old, old_last_votes) {
        var square_size_px = 5;
        if(round_id != round_id_old){
            return [0, upvote_nclicks, downvote_nclicks, 0, {"width": "0px", "height": "0px"}, round_id, 0];
        } else if (old_last_votes != last_votes) {
            var vote_marker = {
                "width": Math.abs(last_votes)*square_size_px+1 + "px", 
                "height": Math.abs(last_votes)*square_size_px+1 + "px", 
                "backgroundColor": (last_votes > 0) ? "#497462" : "#ee2a12", 
                "left": (last_votes < 0) ? 0 : null,
                "top": (last_votes < 0) ? 0 : null,
                "right": (last_votes > 0) ? 0 : null,
                "bottom": (last_votes > 0) ? 0 : null
            };
            return [0, upvote_nclicks, downvote_nclicks, last_votes, vote_marker, round_id, last_votes];
        } else {
            var change = 0;
            if(upvote_nclicks > up_clicks_old){
                change = upvote_nclicks - up_clicks_old;
            } else if(downvote_nclicks > down_clicks_old){
                change = -(downvote_nclicks - down_clicks_old);
            }
            var spare_credits = 100 - all_votes.reduce((a, b) => a + b**2, 0);
            var proposed_new_votes = clicked_votes + change;
            var credit_margin_required = proposed_new_votes ** 2 - clicked_votes ** 2;
            var final_votes = (spare_credits >= credit_margin_required) ? proposed_new_votes : clicked_votes;
            var vote_marker = {
                "width": Math.abs(final_votes)*square_size_px+1 + "px", 
                "height": Math.abs(final_votes)*square_size_px+1 + "px", 
                "backgroundColor": (final_votes > 0) ? "#497462" : "#ee2a12", 
                "left": (final_votes < 0) ? 0 : null,
                "top": (final_votes < 0) ? 0 : null,
                "right": (final_votes > 0) ? 0 : null,
                "bottom": (final_votes > 0) ? 0 : null
            };
            return [final_votes, upvote_nclicks, downvote_nclicks, final_votes, vote_marker, round_id, last_votes];
        }
    }
    """,
    Output({"type": "votes-store", "index": dash.MATCH}, "data"),
    Output({"type":"up-nclick-store","index":dash.MATCH}, "data"),
    Output({"type":"down-nclick-store","index":dash.MATCH}, "data"),
    Output({"type":"vote-square-number","index":dash.MATCH}, "children"),
    Output({"type":"vote-square-marker","index":dash.MATCH}, "style"),
    Output({"type":"store-vote-round-id-old","index":dash.MATCH}, "data"),
    Output({"type":"store-last-votes-old","index":dash.MATCH}, "data"),
    [
        Input({"type": "upvote-button", "index": dash.MATCH}, "n_clicks"),
        Input({"type": "downvote-button", "index": dash.MATCH}, "n_clicks"),
        Input({"type":"store-vote-round-id","index":dash.MATCH}, "data"),
        Input({"type":"store-last-votes","index":dash.MATCH}, "data"),
    ],
    State({"type": "votes-store", "index": dash.ALL}, "data"),
    State({"type": "votes-store", "index": dash.MATCH}, "data"),
    State({"type":"up-nclick-store","index":dash.MATCH}, "data"),
    State({"type":"down-nclick-store","index":dash.MATCH}, "data"),
    State({"type":"store-vote-round-id-old","index":dash.MATCH}, "data"),
    State({"type":"store-last-votes-old","index":dash.MATCH}, "data")
)


# update the graphics for the credit
dash.clientside_callback(
    """
    function(votes) {
        const square_size_px = 8;
        let credit = 100 - votes.reduce((a, b) => a + b*b, 0);
        let credit_width = Math.floor(credit / 5);
        let number_of_row_with_extra_credit = credit % 5;
        let credit_markers = Array.from({length: 5}, (_, i) => i < number_of_row_with_extra_credit ? {width: `${(credit_width+1)*square_size_px+1}px`, height: `${square_size_px+1}px`} : {width: `${credit_width*square_size_px+1}px`, height: `${square_size_px+1}px`});
        return credit_markers;
    }
    """,
    Output({"type":"credit-marker","index":dash.ALL}, "style"),
    Input({"type":"votes-store","index":dash.ALL}, "data"),
)

@dash.callback(
    Output("send-votes-button", "disabled"),
    Output({"type":"downvote-button","index":dash.ALL}, "disabled"),
    Output({"type":"upvote-button","index":dash.ALL}, "disabled"),
    [Input('send-votes-button', 'n_clicks'), Input('store-round-state', 'data')],
    [State({"type":"votes-store","index":dash.ALL}, "data"), State("login", "data")]
)
def send_votes_and_enable_buttons(vote_send_clicks, round_data, votes, login):
    if login is None:
        return True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]
    else:
        if not database_interaction.check_user_id_exists(login["user_id"]):
            return True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]

    ctx = dash.callback_context
    if(ctx.triggered_id == "send-votes-button"):
        if(database_interaction.has_user_voted_in_round(login["user_id"], round_data["round_id"])):
            return True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]
        else:
            if(np.sum(np.abs(votes)) >0):
                for i in range(len(round_data["message_ids"])):
                    database_interaction.add_votes_to_message(round_data["round_id"], round_data["message_ids"][i], votes[i], login["user_id"])
            return True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]
    else: # triggered by store-round-state
        # check whether the user has already voted in this round.
        if(database_interaction.has_user_voted_in_round(login["user_id"], round_data["round_id"])):
            return True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]
        else:
            # disable the options which aren't available. 
            is_row_disabled = [False if m < len(round_data["message_ids"]) else True for m in range(settings.round_comment_pool_size)]
            return False, is_row_disabled, is_row_disabled

@dash.callback(
    Output('previous-messages', 'children'),
    Output('previous-messages-ids', 'data'),
    Output('all-loaded-previous-message-ids', 'data'),
    Output('previous-message-ids-ruled-out', 'data'),
    [Input("store-round-state", "data"), Input('show-more-button', 'n_clicks')],
    State('previous-messages', 'children'),
    State('previous-messages-ids', 'data'),
    State('all-loaded-previous-message-ids', 'data'),
    State('previous-message-ids-ruled-out', 'data'),
)
def update_previous_messages(round_state, show_more_clicks, previous_messages,previous_message_ids,all_loaded_previous_message_ids,ids_ruled_out):
    # get the messages with the most votes for each collection, based on the final round votes.
    ctx = dash.callback_context
    if previous_messages is None:
        previous_messages = []

    # don't update if the round state has updated, but there isn't a round going on and there are previous messages.
    if(ctx.triggered_id == "store-round-state" and not round_state["round_id"] is None and not len(previous_messages) == 0):
        raise dash.exceptions.PreventUpdate
    
    new_winner = ctx.triggered_id == "store-round-state" and round_state["round_id"] is None and not len(previous_messages) == 0

    if new_winner:
        print(previous_message_ids)
        new_messages = database_interaction.fetch_top_messages(count=1,offset=0)
        all_loaded_previous_message_ids.append(new_messages[0].id)
        if(not new_messages[0].previous_message_id is None):
            id_to_remove = new_messages[0].previous_message_id
            ids_ruled_out.append(id_to_remove)
            for i in range(len(previous_message_ids)):
                if previous_message_ids[i] == id_to_remove:
                    previous_message_ids.pop(i)
                    previous_messages.pop(i)
                    break
    else: # loading button clicked
        new_messages = []
        while (len(new_messages) < 10):
            next_message = database_interaction.fetch_top_messages(count=1,offset=len(all_loaded_previous_message_ids))
            if next_message is None or len(next_message) == 0:
                break
            next_message = next_message[0]
            all_loaded_previous_message_ids.append(next_message.id)
            if(not next_message.id in ids_ruled_out):
                new_messages.append(next_message)
            if(not next_message.previous_message_id is None):
                ids_ruled_out.append(next_message.previous_message_id)
    new_content = []
    for m in new_messages:
        if not m is None:
            new_text = html.Div(m.content, className="message-text") if not m.censored else html.Div("CENSORED", className="message-text-previous")
            new_image = html.Div(html.Img(src=m.image, className="image"), className="image-container") if not (m.image is None or m.censored) else None
            text_and_image = html.Div([new_image,new_text],className="message-text-and-image")
            username = database_interaction.fetch_message_sender_name(m.id)
            new_name = dcc.Link("- "+username, href="/users/"+username, className="message-username-previous")
            reply_button = dbc.Button("Reply", id={"type":"reply-button","index":m.id}, className="reply-button", n_clicks=0, color="none")
            reply_button_click_store = dcc.Store(id={"type":"reply-button-nclick-store","index":m.id}, data=0)
            username_reply_and_show_more = html.Div([reply_button,new_name,reply_button_click_store],className="message-previous-username-reply-and-show-more")
            if(m.previous_message_id is None):
                content = text_and_image
            else:
                previous_message = database_interaction.get_message_by_id(m.previous_message_id)
                previous_text = html.Div(previous_message.content, className="message-text-old") if not previous_message.censored else html.Div("CENSORED", className="message-text")
                previous_image = html.Div(html.Img(src=previous_message.image, className="image-small"), className="image-container") if not (previous_message.image is None or previous_message.censored) else None
                previous_text_and_image = html.Div([previous_image,previous_text],className="message-text-and-image")
                content = [previous_text_and_image,text_and_image]
            button = dbc.Button(content,className="previous-message-container-messages", id={"type":"previous-message-show-button","index":m.id}, n_clicks=0, color="none")
            button_clicks = dcc.Store(id={"type":"previous-message-show-button-n-clicks","index":m.id}, data=0)
            new_content.append(html.Div([button,button_clicks,username_reply_and_show_more], className="previous-message-container"))
    new_content = new_content[::-1]
    new_ids = [m.id for m in new_messages][::-1]
    if new_winner:
        return previous_messages + new_content, previous_message_ids + new_ids, all_loaded_previous_message_ids, ids_ruled_out
    else:
        return new_content + previous_messages, new_ids + previous_message_ids, all_loaded_previous_message_ids, ids_ruled_out
    


@dash.callback(
    Output('show-more-modal', 'is_open'),
    Output('show-more-modal-body', 'children'),
    Output("show-more-current-oldest-message-index", "data"),
    Output({"type":"previous-message-show-button-n-clicks","index":dash.ALL}, "data"),
    Input({"type":"voting-message-container","index":dash.ALL}, "n_clicks"),
    Input({"type":"previous-message-show-button","index":dash.ALL}, "n_clicks"),
    Input("show-more-modal-load-older", "n_clicks"),
    State("store-round-state", "data"),
    State("show-more-current-oldest-message-index", "data"),
    State("show-more-modal-body", "children"),
    State({"type":"previous-message-show-button-n-clicks","index":dash.ALL}, "data"),
    prevent_initial_call=True
)
def show_more_message(vote_clicks_open, previous_message_clicks_open, clicks_show_more, store_round_state, oldest_message_id, current_messages, current_previous_message_clicks):
    ctx = dash.callback_context
    print(ctx.triggered_id)
    if ctx.triggered_id == "show-more-modal-load-older":
        earlier_message_id = oldest_message_id
        if earlier_message_id is None:
            raise dash.exceptions.PreventUpdate
    else:
        current_messages=[]
        if(ctx.triggered_id["type"] == "voting-message-container"):
            index = ctx.triggered_id['index']
            earlier_message_id = store_round_state["message_ids"][index] # the buttons are indexes (e.g., 1-5)
        else:
            if(len(current_previous_message_clicks)==len(previous_message_clicks_open)):
                if all([previous_message_clicks_open[i]==current_previous_message_clicks[i] for i in range(len(previous_message_clicks_open))]):
                    raise dash.exceptions.PreventUpdate
            id = ctx.triggered_id['index']
            earlier_message_id = id # in the previous messages the button is saved with the id 
    new_content = []
    for j in range(5):
        m = database_interaction.get_message_by_id(earlier_message_id)
        new_text = html.Div(m.content, className="message-text") if not m.censored else html.Div("CENSORED", className="message-text-previous")
        new_image = html.Div(html.Img(src=m.image, className="image"), className="image-container") if not (m.image is None or m.censored) else None
        text_and_image = html.Div([new_image,new_text],className="message-text-and-image")
        new_content.append(html.Div(text_and_image,className="previous-message-container-messages"))
        if not m.previous_message_id is None:
            earlier_message_id = m.previous_message_id
        else:
            earlier_message_id = None
            break
    
    combined_content = new_content[::-1] + current_messages
    print(previous_message_clicks_open)
    return True, combined_content, earlier_message_id, previous_message_clicks_open

dash.clientside_callback(
    """
    function() {
        messageInput = document.querySelector('#message-input');
        if (messageInput) {
            messageInput.focus();
        } else {
            console.log("message-input not found");
        }
        return;
    }
    """,
    Output("hidden-div-reply-focus", "children"),
    Input({"type":"reply-button","index":dash.ALL}, "n_clicks"),
    prevent_initial_call=True
)

# if the user hits reply, update input-in-reply-message with the old message.
@dash.callback(
    Output("input-in-reply-message", "children"),
    Output("input-in-reply-message-container", "style"),
    Output({"type":"reply-button-nclick-store","index":dash.ALL}, "data"),
    Output("reply-message-id", "data"),
    [Input({"type":"reply-button","index":dash.ALL}, "n_clicks")],
    [Input({"type":"reply-button-nclick-store","index":dash.ALL}, "data")],
    Input("cancel-reply-button", "n_clicks"),
    Input("message-sent-trigger", "children"),
    prevent_initial_call=True
)
def reply_to_message(n_clicks_reply, n_clicks_old, message_was_sent, n_clicks_cancel):
    # check which button was clicked.
    ctx = dash.callback_context
    if ctx.triggered_id == "cancel-reply-button" or ctx.triggered_id == "message-sent-trigger":
        return "", {"display":"none"}, n_clicks_reply, "NA"
    else:
        if n_clicks_reply is None:
            raise dash.exceptions.PreventUpdate
        else:
            any_triggered = False
            for i in range(len(n_clicks_reply)):
                if not n_clicks_reply[i]==n_clicks_old[i]:
                    any_triggered = True
                    break
            if any_triggered: 
                index = ctx.triggered_id["index"]
                m = database_interaction.get_message_by_id(index)
                if m is None:
                    return "", {"display":"none"}, n_clicks_reply, "NA"
                else:
                    new_text = html.Div(m.content, className="message-text-old") if not m.censored else html.Div("CENSORED", className="message-text-previous")
                    new_image = html.Div(html.Img(src=m.image, className="image-small"), className="image-container") if not (m.image is None or m.censored) else None
                    text_and_image = html.Div([new_image,new_text],className="message-text-and-image")
                    return html.Div(text_and_image,className="previous-message-container-messages"), {"display":"flex"}, n_clicks_reply, index
            else:
                raise dash.exceptions.PreventUpdate