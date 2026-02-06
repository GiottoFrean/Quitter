import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import sqlalchemy
from database.database import Base, SessionLocal, engine
from dash_app.utils import database_interaction
import dash_bootstrap_components as dbc
import json
import requests
import os

app_config = json.load(open("dash_app/app_config.json"))
# Override sensitive/config values from environment if provided
_site = os.environ.get("RECAPTCHA_SITE_KEY")
_secret = os.environ.get("RECAPTCHA_SECRET_KEY")
_debug = os.environ.get("DEBUG")
_disable_recaptcha = os.environ.get("DISABLE_RECAPTCHA")
if _site:
    app_config["recaptcha_site_key"] = _site
if _secret:
    app_config["recaptcha_secret_key"] = _secret
if _debug is not None:
    app_config["debug"] = _debug.lower() in ("1", "true", "yes", "on")
disable_recaptcha = False
if _disable_recaptcha is not None:
    disable_recaptcha = _disable_recaptcha.lower() in ("1", "true", "yes", "on")

# Determine whether reCAPTCHA should be enabled
recaptcha_enabled = (not app_config["debug"]) and (not disable_recaptcha)

# Build external scripts: load reCAPTCHA only when enabled
recaptcha_url = "https://www.google.com/recaptcha/api.js?render={}".format(app_config["recaptcha_site_key"])
external_scripts = [recaptcha_url] if recaptcha_enabled else []

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
    external_scripts=external_scripts,
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
                dcc.Link([html.Img(src="/assets/logo.svg",className="logo-header"),html.Div('Quitter.app')], href='/', className="nav-quitter"), 
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

# Optional: run the state updater loop inside the web process when enabled
enable_state_worker = os.environ.get("ENABLE_STATE_WORKER", "false").lower() in ("1", "true", "yes", "on")
if enable_state_worker:
    try:
        import threading, time
        from central_script import update_state
        from database.database import SessionLocal

        def _state_worker_loop():
            while True:
                try:
                    session = SessionLocal()
                    update_state(session)
                    session.close()
                    time.sleep(1)
                except Exception as e:
                    print("[state-worker] error:", e)
                    time.sleep(5)

        # Avoid double-start when Flask reloader is active
        is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        if (not app_config.get("debug", False)) or is_reloader_child:
            threading.Thread(target=_state_worker_loop, daemon=True).start()
            print("[state-worker] started in web process")
    except Exception as e:
        print("[state-worker] failed to start:", e)

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
            if (typeof grecaptcha === 'undefined') {
                return 'debug-token';
            }
            return new Promise(
                function(resolve, reject) {
                    grecaptcha.ready(function() {
                        grecaptcha.execute('_site-key', {action: 'submit'}).then(function(token) {
                            resolve(token);
                        }).catch(function(){
                            resolve('debug-token');
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
    
    if username_login is None or password_login is None:
        return dash.no_update, dash.no_update
    # reCAPTCHA: verify only when enabled; otherwise accept a dummy token
    if recaptcha_enabled:
        if not recaptcha_token:
            return dash.no_update, "Recaptcha failed"
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data = {
                'secret': app_config["recaptcha_secret_key"],
                'response': recaptcha_token
            }
        )
        result = response.json()
        if not result.get("success"):
            return dash.no_update, "Recaptcha failed"
        if not result.get("score", 0) > 0.5:
            return dash.no_update, "Recaptcha failed"
    else:
        if not recaptcha_token:
            recaptcha_token = "debug-token"
    
    user = database_interaction.get_user(username_login)
    if user is None:
        return dash.no_update, "User does not exist"
    
    if not user.password_hash == database_interaction.hash_password(password_login):
        return dash.no_update, "Wrong password"
    
    return {"user_id": user.id}, "You are logged in!"

dash.clientside_callback(
    """
    function(data) {
        if (data) {
            if (typeof grecaptcha === 'undefined') {
                return 'debug-token';
            }
            return new Promise(
                function(resolve, reject) {
                    grecaptcha.ready(function() {
                        grecaptcha.execute('_site-key', {action: 'submit'}).then(function(token) {
                            resolve(token);
                        }).catch(function(){
                            resolve('debug-token');
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
    Output("login", "data", allow_duplicate=True),
    Output("register-error-message", "children"),
    [Input("register-button", "n_clicks")],
    [State("register-recaptcha-send", "data"), State("username-register", "value"), State("password-register", "value"), State("password-register-confirm", "value")],
    prevent_initial_call=True
)
def register(register_clicks, recaptcha_token, username_register, password_register, password_register_confirm):
    ctx = dash.callback_context
    print("[register] triggered by:", ctx.triggered_id, "token:", bool(recaptcha_token), "username:", username_register)
    if not username_register or not password_register or not password_register_confirm:
        return dash.no_update, "Please fill all fields"

    # If reCAPTCHA is disabled, allow a dummy token; otherwise verify
    if recaptcha_enabled:
        if not recaptcha_token:
            return dash.no_update, "Recaptcha failed"
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data = {
                'secret': app_config["recaptcha_secret_key"],
                'response': recaptcha_token
            }
        )
        result = response.json()

        if not result.get("success"):
            return dash.no_update, "Recaptcha failed"
        if not result.get("score", 0) > 0.5:
            return dash.no_update, "Recaptcha failed"
    else:
        if not recaptcha_token:
            recaptcha_token = "debug-token"
    
    user = database_interaction.get_user(username_register)
    if not user is None:
        return dash.no_update, "User already exists"
    
    if password_register != password_register_confirm:
        return dash.no_update, "Passwords do not match"
    
    if len(username_register) > 25:
        return dash.no_update, "username can be at most 25 characters"
    
    #check username is just letters, numbers or underscores
    username_no_underscores = username_register.replace("_","")
    if not username_no_underscores.isalnum():
        return dash.no_update, "username can only contain letters, numbers, underscores"

    print("[register] creating user:", username_register)
    database_interaction.create_user(username_register, password_register)
    user_id = database_interaction.get_user(username_register).id
    print("[register] success; user_id:", user_id)
    return {"user_id": user_id}, "You are now registered & logged in!"

if __name__ == '__main__':
    app.run(debug=app_config["debug"],port=5000,host="0.0.0.0")