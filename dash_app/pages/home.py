import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import sqlalchemy
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

app_config = json.load(open("dash_app/app_config.json"))

dash.register_page(__name__,path="/")

# voting row is a row with a message, a voting square, and up/down vote buttons
def make_voting_row(index):
    message_container = dbc.Button(
        html.Div(id={"type":"message-text","index":index}, className="message-text"),
        id={"type":"voting-message-container","index":index}, 
        className="voting-message-container", 
        n_clicks=0, 
        color="none")
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
                        html.Div(html.Div([make_credit_row(index) for index in range(5)]), className="credits-container"),
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
        html.Div(
            id="previous-messages",
            className="previous-messages"
        ),
        html.Div([dbc.Button("Show more", id="show-more-button", className="show-more-button", n_clicks=0, color="none")],className="show-more-button-container")
    ]
)

input_message_layout = html.Div(
    className='fixed-input-area', 
    children=[
        html.Div(
            children=[
                dcc.Store(id="message-data-store"),
                dcc.Store(id="send-message"),
                dcc.Store(id="recaptcha-send-message"),
                html.Div(id="send-message-output"),
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
            ],
            className="message-input-and-button"
        )
    ]
)

show_more_modal = dbc.Modal(
    [
        dbc.ModalHeader([]),
        dbc.ModalBody("This is the content of the modal", id="show-more-modal-body", className="show-more-modal-body"),
    ],
    id="show-more-modal",
    is_open=False
)

refresh_component = dcc.Interval(id='home-refresh-interval', interval=1000, n_intervals=0)
store_round_state = dcc.Store(id='store-round-state', data={"round_id":-1,"message_ids":[],"messages":[]})
round_state_switch_time = dcc.Store(id='round-state-switch-time', data=None)


layout = html.Div(
    [
        application_status_layout,
        credit_and_voting_layout,
        previous_messages_layout,
        input_message_layout,
        refresh_component,
        store_round_state,
        show_more_modal,
        round_state_switch_time
    ]
)

# prevent the enter key from adding a new line, unless pressed with shift. 
dash.clientside_callback(
    """
    function(dummy) {
        var messageInput = document.querySelector('#message-input');
        if (messageInput) {
            messageInput.addEventListener('keydown', function (e) {
                if (e.keyCode === 13 && !e.shiftKey) {
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
    function(n_events, send_clicks, enterEvent, text, send_clicks_store) {
        if (enterEvent && enterEvent.key === "Enter" && !enterEvent.shiftKey) {
            return [{"message": text}, send_clicks];
        } else if (send_clicks > send_clicks_store) {
            return [{"message": text}, send_clicks];
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
    State("send-clicks", "data"),
)

# process a new message, and get ready to send if it looks alright.
@dash.callback(
    Output('message-input', 'error'),
    Output('message-input', 'value'),
    Output('send-message', 'data'),
    [Input('message-data-store', 'data')]
)
def check_message(message_data):
    if(not message_data == None):
        message = message_data["message"]
        lines = message.split('\n')
        if len(message) > settings.max_characters:
            return "Error: message has too many characters. Please keep it to "+str(settings.max_characters)+" at most.", dash.no_update, dash.no_update
        else:
            if(len(message) > 0):
                return None, "", message
    return dash.no_update, dash.no_update, dash.no_update


# update the recaptcha data store when message-send is updated. The first time this will be empty. 
dash.clientside_callback(
    """
    function(data) {
        if (data) {
            return new Promise(
                function(resolve, reject) {
                    grecaptcha.ready(function() {
                        grecaptcha.execute('_site-key', {action: 'submit'}).then(function(token) {
                            resolve(token);
                        });
                    });
                }
            )
        }
        return '';
    }
    """.replace("_site-key",app_config["recaptcha_site_key"]),
    Output('recaptcha-send-message', 'data'),
    Input('send-message', 'data')
)


@dash.callback(
    Output("send-message-output", "children"),
    [Input('recaptcha-send-message', 'data')],
    [State('send-message', 'data')]
)
def send_message(recaptcha_token, message):
    if(not message is None):
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data = {
                'secret': app_config["recaptcha_secret_key"],
                'response': recaptcha_token
            }
        )
        result = response.json()
        if((result["success"] and result["score"] > 0.5) or app_config["debug"]==True):
            database_interaction.add_comment(message+str(result))
    return dash.no_update

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
        collection_id = state.collection_id - 1 # -1 because the current collection is the one being run, not the one that has just finished
        collection_status = state.collection_status
        collection_count = state.collection_count
        collection_end_time = state.collection_end_time
        round_status = state.round_status
        round_voters = state.round_voters
        round_end_time = state.round_end_time
        round_id = state.round_id

        if round_status == "collecting":
            return html.Div(f"Status: Collection {collection_id} is being run. Waiting for minimum voters ({round_voters} / {settings.minimum_voters_for_round_to_proceed_to_timing})", className="application-status-text")
        elif round_status == "waiting":
            time_remaining = round_end_time - datetime.datetime.now(pytz.utc).replace(tzinfo=None)
            time_remaining_seconds = max(0,int(round(time_remaining.total_seconds(), 0)))
            return html.Div(f"Status: Collected from {round_voters} voters for collection {collection_id}. {time_remaining_seconds} seconds left", className="application-status-text")
        else:
            if collection_status == "collecting":
                return html.Div(f"Status: Collecting comments ({collection_count} / {settings.minimum_comments_for_collection_to_proceed_to_timing})", className="application-status-text")
            elif collection_status == "waiting":
                time_remaining = collection_end_time - datetime.datetime.now(pytz.utc).replace(tzinfo=None)
                time_remaining_seconds = max(0,int(round(time_remaining.total_seconds(), 0)))
                return html.Div(f"Status: Collecting comments. {time_remaining_seconds} seconds left", className="application-status-text")

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
    if(database_state.round_id != current_state["round_id"]):
        # the round has changed.
        current_time = datetime.datetime.now(pytz.utc).replace(tzinfo=None)
        action = "nothing"
        if(switch_time is None):
            if (len(current_state["messages"]) > 0):
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
            messages = database_interaction.fetch_messages_in_round()
            if(len(messages) == 1):
                new_state["message_ids"] = []
                new_state["messages"] = []
            else:   
                new_state["message_ids"] = [m.id for m in messages]
                new_state["messages"] = [m.content for m in messages]
            return new_state, [database_state.round_id for i in range(settings.round_comment_pool_size)], [dash.no_update for i in range(settings.round_comment_pool_size)], None

    raise dash.exceptions.PreventUpdate

# sets the display of the voting messages (whether to show them, etc)
@dash.callback(
    Output({"type":"message-text","index":dash.ALL}, "children"),
    Output({"type":"voting-row","index":dash.ALL}, "className"),
    Output("credits-and-vote-show-hide-wrapper", "className"),
    [Input("store-round-state", "data")],
)
def update_voting_stuff(state):
    messages = state.get("messages", [])
    content = [messages[m] if m < len(messages) else "" for m in range(settings.round_comment_pool_size)]
    rows_open = [True if m < len(messages) else False for m in range(settings.round_comment_pool_size)]
    rows_classnames = ["voting-row show" if o else "voting-row hide" for o in rows_open]
    show_credit_and_voting_button = True if len(messages) > 0 else False
    credit_and_voting_classname = "credits-and-vote-show-hide-wrapper show" if show_credit_and_voting_button else "credits-and-vote-show-hide-wrapper hide"
    return content, rows_classnames, credit_and_voting_classname


dash.clientside_callback(
    """
    function(upvote_nclicks, downvote_nclicks, round_id, last_votes, all_votes, clicked_votes, up_clicks_old, down_clicks_old, round_id_old, old_last_votes) {
        var square_size_px = 8;
        console.log(last_votes, old_last_votes);
        if(round_id != round_id_old){
            return [0, upvote_nclicks, downvote_nclicks, 0, {"width": "0px", "height": "0px"}, round_id, last_votes];
        } else if (old_last_votes != last_votes) {
            var vote_marker = {
                "width": Math.abs(last_votes)*square_size_px + "px", 
                "height": Math.abs(last_votes)*square_size_px + "px", 
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
                "width": Math.abs(final_votes)*square_size_px + "px", 
                "height": Math.abs(final_votes)*square_size_px + "px", 
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
        let credit_markers = Array.from({length: 5}, (_, i) => i < number_of_row_with_extra_credit ? {width: `${(credit_width+1)*square_size_px+2}px`, height: `${square_size_px+2}px`} : {width: `${credit_width*square_size_px+1}px`, height: `${square_size_px+1}px`});
        return credit_markers;
    }
    """,
    Output({"type":"credit-marker","index":dash.ALL}, "style"),
    Input({"type":"votes-store","index":dash.ALL}, "data"),
)

@dash.callback(
    Output('send-votes', 'data'),
    Output("send-votes-button", "disabled"),
    Output({"type":"downvote-button","index":dash.ALL}, "disabled"),
    Output({"type":"upvote-button","index":dash.ALL}, "disabled"),
    [Input('send-votes-button', 'n_clicks'), Input('store-round-state', 'data')],
    State({"type":"votes-store","index":dash.ALL}, "data"),
)
def send_votes_and_enable_buttons(vote_send_clicks, round_data, votes):
    ctx = dash.callback_context
    if(ctx.triggered_id == "send-votes-button"):
        return votes, True, [True for i in range(settings.round_comment_pool_size)], [True for i in range(settings.round_comment_pool_size)]
    else: # triggered by store-round-state
        is_row_disabled = [False if m < len(round_data["message_ids"]) else True for m in range(settings.round_comment_pool_size)]
        return dash.no_update, False, is_row_disabled, is_row_disabled


# update the recaptcha data store when send-votes is updated. The first time this will be empty. 
dash.clientside_callback(
    """
    function(data) {
        if (data) {
            return new Promise(
                function(resolve, reject) {
                    grecaptcha.ready(function() {
                        grecaptcha.execute('_site-key', {action: 'submit'}).then(function(token) {
                            resolve(token);
                        });
                    });
                }
            )
        }
        return '';
    }
    """.replace("_site-key",app_config["recaptcha_site_key"]),
    Output('recaptcha-send-votes', 'data'),
    Input('send-votes', 'data')
)


@dash.callback(
    Output("send-votes-output", "children"),
    [Input('recaptcha-send-votes', 'data')],
    [State('send-votes', 'data'), State('store-round-state', 'data')]
)
def add_votes(recaptcha_token, votes, round_data):
    if(not votes is None):
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data = {
                'secret': app_config["recaptcha_secret_key"],
                'response': recaptcha_token
            }
        )
        result = response.json()
        if((result["success"] and result["score"] > 0.5) or app_config["debug"]==True):
            if(np.sum(np.abs(votes)) >0):
                for i in range(len(round_data["message_ids"])):
                    database_interaction.add_votes_to_message(round_data["round_id"],round_data["message_ids"][i],votes[i])
    return dash.no_update


@dash.callback(
    Output('previous-messages', 'children'),
    [Input("store-round-state", "data"), Input('show-more-button', 'n_clicks')],
    State('previous-messages', 'children'),
)
def update_previous_messages(round_state, show_more_clicks, previous_messages):
    # get the messages with the most votes for each collection, based on the final round votes.
    ctx = dash.callback_context
    if(ctx.triggered_id == "show-more-button"):
        messages = database_interaction.fetch_top_messages(offset=len(previous_messages))
        return previous_messages + [html.Div(html.Div(message.content, className="message-text-previous"),className="message-container-previous") for message in messages]
    elif(ctx.triggered_id == "store-round-state"):
        if(previous_messages is None):
            messages = database_interaction.fetch_top_messages()
            return [html.Div(html.Div(message.content, className="message-text-previous"),className="message-container-previous") for message in messages]
        elif(len(round_state["messages"]) == 0): # round has just been updated, so add the top message
            messages = database_interaction.fetch_top_messages(1)
            if(len(messages) > 0):
                return [html.Div(html.Div(messages[0].content, className="message-text-previous"),className="message-container-previous")] + previous_messages
            else:
                return dash.no_update
        else:
            return dash.no_update


@dash.callback(
    Output('show-more-modal', 'is_open'),
    Output('show-more-modal-body', 'children'),
    [Input({"type":"voting-message-container","index":dash.ALL}, "n_clicks")],
    [State({"type":"message-text","index":dash.ALL}, "children")],
    prevent_initial_call=True
)
def show_more_message(clicks_show, messages):
    ctx = dash.callback_context
    index = ctx.triggered_id['index']
    return True, messages[int(index)]