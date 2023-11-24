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

app_config = json.load(open("dash_app/app_config.json"))

dash.register_page(__name__,path="/login", title="login")

layout = html.Div(
    [
        html.Br(),
        html.Div(id="currently-loggedin"),
        dcc.Input(
            id="username-login",
            className="login-input",
            placeholder="Username",
            type="text",
        ),
        dcc.Input(
            id="password-login",
            className="login-input",
            placeholder="Password",
            type="password",
        ),
        html.Button("Login", id="login-button", className="login-button"),
        dcc.Loading(
            id="login-loading",
            children=[
                html.Div(id="login-error-message", className="login-error"),
            ],
            type="circle",
            color="red",
            fullscreen=False,
            style={"width": "50px", "height": "50px"}
        ),
        html.Br(),
        html.Div("Not registered yet? "),
        dcc.Link("Register here", href="/register", className="nav-link-blue"),
        html.Br(),
        html.Div("Or"),
        html.Button("Logout", id="logout-button", className="logout-button"),
    ],
    className="login-form",
)

@dash.callback(
    Output("currently-loggedin", "children"),
    Input("login", "data"),
)
def tell_who_is_logged_in(login):
    if login is None:
        return "You aren't logged in"
    else:
        login_name = database_interaction.get_username_from_id(login["user_id"])
        if login_name is None:
            return "You aren't logged in"
        else:
            return html.Div([html.Div("Logged in as: "), dcc.Link(login_name, href="/users/"+login_name, className="nav-link")])
