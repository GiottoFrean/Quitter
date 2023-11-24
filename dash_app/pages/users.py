import dash
from dash import html, dcc
from dash_app.utils import database_interaction
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

dash.register_page(__name__, path_template="/users/<user_name>")

def make_message_row_from_message(m):
    new_text = html.Div(m.content, className="user-message-text") if not m.censored else html.Div("CENSORED", className="user-message-text")
    in_round_count, total_round_count = database_interaction.get_highest_round_for_message(m)
    new_ratio = html.Div("("+str(in_round_count)+"/"+str(total_round_count)+")", className="user-message-ratio")
    return html.Div([new_text,new_ratio],className="user-message-container")

def layout(user_name=None):
    return html.Div(
        id="user-page-messages-container",
        className="user-messages-container",
        children=[
            html.Div(user_name, className="user-page-title"),
            dcc.Store(id='user_page-user_name', data=user_name),
            html.Div(
                id="user-page-messages",
                children = [],
                className="user-messages"
            ),
            html.Div([dbc.Button("Show more", id="user-page-show-more-button", className="show-more-button", n_clicks=0, color="none")],className="show-more-button-container")
        ]
    )

@dash.callback(
    Output('user-page-messages', 'children'),
    [Input('user-page-show-more-button', 'n_clicks')],
    [State('user-page-messages', 'children'),State('user_page-user_name', 'data')]
)
def update_previous_messages(show_more_clicks, previous_messages, user_name):
    # get the messages with the most votes for each collection, based on the final round votes.
    new_messages = database_interaction.get_messages_for_user(user_name,count=10,offset=len(previous_messages))
    new_content = [make_message_row_from_message(m) for m in new_messages]
    return previous_messages + new_content