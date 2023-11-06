import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import sqlalchemy
from database import Base, SessionLocal, engine
from dash_app.utils import database_interaction
import dash_bootstrap_components as dbc
import json

app_config = json.load(open("dash_app/app_config.json"))

app = dash.Dash(
    __name__, 
    use_pages=True, 
    pages_folder="dash_app/pages", 
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    assets_folder="dash_app/static/",
    meta_tags=[
        {"http-equiv": "content-language", "content": "en"},
        {
            "name": "description",
            "content": "Quitter",
        },
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
    external_scripts=["https://www.google.com/recaptcha/api.js?render=_site-key".replace("_site-key",app_config["recaptcha_site_key"])],
    update_title=None,
)
app._favicon = "logo.svg"
app.title = "Quitter"

navbar = html.Div(
    id="fixed-header-bar",
    className='fixed-header-bar',
    children=[
        html.Div(
            [
                dcc.Link([html.Img(src="/assets/logo.svg",className="logo-header"),html.Div('Quitter')], href='/', className="nav-quitter"), 
            ],
            className="nav-quitter-container"),
        html.Div(
            children=[
                dcc.Link('Home', href='/', className="nav-link"),
                dcc.Link('About', href='/about', className="nav-link")
            ],
            className="nav-links"
        ),
    ]
)

server = app.server

app.layout = html.Div([
    html.Meta(name='description', content='Quadratic voting twitter'),
    html.Title('Quitter'),
    html.Div(
        children=[
            html.Link(href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css', rel='stylesheet'),
            navbar,
            dash.page_container,
            html.Script(src='dash_app/static/scroll_header.js')
        ],
        className="overall-container"
    )
])

if __name__ == '__main__':
    app.run(debug=app_config["debug"],port=5000,host="0.0.0.0")