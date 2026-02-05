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

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database settings in database/local.py
# Configure reCAPTCHA keys in dash_app/recaptcha_config.json and dash_app/app_config.json

# Initialize database (first time only)
python central_script.py reset

# Run the central script (manages voting rounds)
python central_script.py &

# Run the web app (in a separate process)
python app.py
```
