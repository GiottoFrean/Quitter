import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import sqlalchemy
from database.database import Base, SessionLocal, engine
from dash_app.utils import database_interaction
import dash_bootstrap_components as dbc
import json
import requests

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
            "content": "Quadratic voting twitter",
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
                dcc.Link('About', href='/about', className="nav-link"),
                dcc.Link('Login', href='/login', className="nav-link")
            ],
            className="nav-links"
        ),
    ]
)

server = app.server

app.layout = html.Div([
    html.Meta(name='description', content='Quadratic voting twitter'),
    html.Title('Quitter'),
    html.Meta(name="og:title", content="Quitter"),
    html.Meta(name="og:description", content="Quadratic voting twitter"),
    html.Meta(name="og:image", content="https://quitter.app/assets/logo.svg"),
    html.Meta(name="og:url", content="https://quitter.app/"),
    html.Meta(name="twitter:card", content="summary_large_image"),
    html.Meta(name="twitter:site", content="@Quitter_app"),
    html.Meta(name="twitter:title", content="Quitter"),
    html.Meta(name="twitter:description", content="Quadratic voting twitter"),
    html.Meta(name="twitter:image", content="https://quitter.app/assets/logo.svg"),
    html.Meta(name="twitter:url", content="https://quitter.app/"),
    dcc.Store(id='login-recaptcha-send'),
    dcc.Store(id='register-recaptcha-send'),
    dcc.Store(id='login', storage_type='local'),
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
    Output('login-recaptcha-send', 'data'),
    Input("login-button", "n_clicks")
)

@dash.callback(
    Output("login", "data", allow_duplicate=True),
    Output("login-error-message", "children"),
    [Input("login-recaptcha-send", "data"), Input("logout-button", "n_clicks")],
    [State("username-login", "value"), State("password-login", "value")],
    prevent_initial_call=True
)
def login(recaptcha_token, logout_clicks, username_login, password_login):
    ctx = dash.callback_context
    if(ctx.triggered_id == "logout-button" and logout_clicks is not None):
        return None, "You are logged out"

    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data = {
            'secret': app_config["recaptcha_secret_key"],
            'response': recaptcha_token
        }
    )
    result = response.json()
    if((result["success"] and result["score"] > 0.5) or app_config["debug"]==True):
        if username_login is None or password_login is None:
            return dash.no_update, dash.no_update
        else:
            user = database_interaction.get_user(username_login)
            if user is None:
                return dash.no_update, "User does not exist"
            elif user.password_hash == database_interaction.hash_password(password_login):
                return {"user_id": user.id}, "You are logged in!"
            else:
                return dash.no_update, "Wrong password"

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
    Output('register-recaptcha-send', 'data'),
    Input("register-button", "n_clicks")
)

@dash.callback(
    Output("login", "data"),
    Output("register-error-message", "children"),
    [Input("register-recaptcha-send", "data")],
    [State("username-register", "value"), State("password-register", "value"), State("password-register-confirm", "value")],
)
def register(recaptcha_token, username_register, password_register, password_register_confirm):
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data = {
            'secret': app_config["recaptcha_secret_key"],
            'response': recaptcha_token
        }
    )
    result = response.json()
    if((result["success"] and result["score"] > 0.5) or app_config["debug"]==True):
        if username_register is None or password_register is None or password_register_confirm is None:
            return dash.no_update, dash.no_update
        else:
            user = database_interaction.get_user(username_register)
            if user is None:
                if password_register != password_register_confirm:
                    return dash.no_update, "Passwords do not match"
                database_interaction.create_user(username_register, password_register)
                user_id = database_interaction.get_user(username_register).id
                return {"user_id": user_id}, "You are now registered & logged in!"
            else:
                return dash.no_update, "User already exists"
    

if __name__ == '__main__':
    app.run(debug=app_config["debug"],port=5000,host="0.0.0.0")