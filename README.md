# Quitter

A social media platform which uses quadratic voting to select content. Anonymous posts compete in elimination rounds.

## How It Works

Users get 100 voting credits per round to spend on posts they value. Votes cost credits quadratically (1 vote = 1 credit, 2 votes = 4 credits, 3 votes = 9 credits, etc.), encouraging you to spread votes across multiple posts rather than piling onto one.

All posts are anonymous, so content is judged on merit alone. Posts advance through rounds based on votes until a winner emerges. Every hour or so this process restarts.

## Why?

- **Overwhelming content**: On Quitter only the stuff that matters makes it, no more reading unfiltered rubbish
- **Bias towards frequent users**: Every user has a fixed influence in the voting process. Other platforms let users like as much as they want
- **Popularity over quality**: All posts are anonymous, so content is promoted based on its merit, not the popularity of the author
- **Tyrannies**: Quitter doesn't risk being skewed by a tiny group of users, while also avoiding capture by a majority, thanks to quadratic voting

## Tech Stack

- **Frontend**: Dash (Plotly) with Bootstrap
- **Backend**: Flask + SQLAlchemy
- **Database**: PostgreSQL
- **Security**: reCAPTCHA integration

## Installation

### 1. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database and Set Password

Start the PostgreSQL prompt:
```bash
sudo -u postgres psql
```

Create the database and set a password:
```sql
CREATE DATABASE quitter_db;
ALTER USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE quitter_db TO postgres;
\q
```

### 3. Configure Database Connection

Edit `database/local.py` and update the credentials:
```python
db_params = {
    'host': 'localhost',
    'dbname': 'quitter_db',
    'user': 'postgres',
    'password': 'your_password',  # Use the password you set above
}
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
python central_script.py reset
```

### 6. Run the Application

You need two terminal windows:

**Terminal 1** - Central script (manages voting rounds):
```bash
python central_script.py
```

**Terminal 2** - Web application:
```bash
python app.py
```

The app will be available at `http://localhost:8050`

### Optional: Enable reCAPTCHA

Get reCAPTCHA keys from [Google reCAPTCHA](https://www.google.com/recaptcha) and update `dash_app/app_config.json` with your site and secret keys.
