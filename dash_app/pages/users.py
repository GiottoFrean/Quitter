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
    if user_name == "AreCatsEdible":
        user_name = "AreCatsEdible?"
    return html.Div(
        id="user-page-messages-container",
        className="user-messages-container",
        children=[
            html.Div(user_name, className="user-page-title"),
            html.Div([dbc.Button("Show more", id="user-page-show-more-button", className="show-more-button", n_clicks=0, color="none")],className="show-more-button-container"),
            dcc.Store(id='user_page-user_name', data=user_name),
            html.Div(
                id="user-page-messages",
                children = [],
                className="user-messages"
            )
        ]
    )

@dash.callback(
    Output('user-page-messages', 'children'),
    [Input('user-page-show-more-button', 'n_clicks')],
    [State('user-page-messages', 'children'),State('user_page-user_name', 'data')]
)
def update_previous_messages(show_more_clicks, previous_messages, user_name):
    new_messages = database_interaction.get_messages_for_user(user_name,count=10,offset=len(previous_messages))
    new_content = []
    for m in new_messages:
        if not m is None:
            new_text = html.Div(m.content, className="message-text") if not m.censored else html.Div("CENSORED", className="message-text-previous")
            new_image = html.Div(html.Img(src=m.image, className="image"), className="image-container") if not (m.image is None or m.censored) else None
            text_and_image = html.Div([new_image,new_text],className="message-text-and-image")
            higest_round, total_rounds = database_interaction.get_highest_round_for_message(m)
            new_ratio = html.Div("("+str(higest_round)+"/"+str(total_rounds)+")", className="message-ratio-previous")
            if(m.previous_message_id is None):
                content = text_and_image
            else:
                previous_message = database_interaction.get_message_by_id(m.previous_message_id)
                previous_text = html.Div(previous_message.content, className="message-text-old") if not previous_message.censored else html.Div("CENSORED", className="message-text")
                previous_image = html.Div(html.Img(src=previous_message.image, className="image-small"), className="image-container") if not (previous_message.image is None or previous_message.censored) else None
                previous_text_and_image = html.Div([previous_image,previous_text],className="message-text-and-image")
                content = [previous_text_and_image,text_and_image]
            new_content.append(html.Div([html.Div(content,className="previous-message-container-messages"),new_ratio], className="previous-message-container"))
    new_content = new_content[::-1]
    return new_content + previous_messages