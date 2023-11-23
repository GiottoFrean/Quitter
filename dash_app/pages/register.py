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

dash.register_page(__name__,path="/register", title="register")

layout = html.Div(
    [
        dcc.Input(
            id="username-register",
            className="register-input",
            placeholder="Username",
            type="text",
        ),
        dcc.Input(
            id="password-register",
            className="register-input",
            placeholder="Password",
            type="password",
        ),
        dcc.Input(
            id="password-register-confirm",
            className="register-input",
            placeholder="Password",
            type="password",
        ),
        html.Button("Register", id="register-button", className="register-button"),
        dcc.Loading(
            id="register-loading",
            children=[
                html.Div(id="register-error-message", className="register-error"),
            ],
            type="circle",
            color="red",
            fullscreen=False,
            style={"width": "50px", "height": "50px"}
        )
    ],
    className="register-form",
)