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
import plotly.graph_objects as go

#dash.register_page(__name__,path="/votes")

# layout = html.Div(
#     [
#         html.Div("This page is for exploring the results from the last round of voting."),
#         html.Div("The number is the total votes for that message.", className="vote-page-description"),
#         html.Div(
#             id="vote-page-messages",
#             className="previous-messages"
#         ),
#     ],
#     className = "vote-page"
# )

# @dash.callback(
#     Output("vote-page-messages", "children"),
#     Input("vote-page-messages", "id")
# )
# def update_graph(n_clicks):
#     messages, votes = database_interaction.fetch_last_round_and_votes()
#     return [html.Div([html.Div(messages[i], className="message-text-previous"),html.Div(votes[i], className="message-votes-previous")],className="message-container-previous") for i in range(len(messages))]