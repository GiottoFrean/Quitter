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

dash.register_page(__name__,path="/about")

logo = html.Div(html.Img(src="/assets/logo.svg",className="logo-about"), className="logo-about-container")

# explanation1 = dcc.Markdown(
#     r'''
    
#     Welcome to Quitter, a unique social media platform powered by quadratic voting.

#     #### How does it work?

#     Quitter removes the traditional 'like' system and replaces it with a voting mechanism.
#     Posts are thinned down in a series of rounds, with a single one being left at the end.
#     This is done using in a way which incentivises you to vote in accordance with your actual preferences. 

#     #### Why is this a good idea?

#     Quitter addresses several issues prevalent in conventional social media platforms:

#     - **Overwhelming content:** Quitter filters through the noise, guiding you towards content that truly matters.
#     - **Bias towards frequent users:** Quitter ensures that content promotion is not skewed towards those who use the platform most often. Each user has a fixed influence. 
#     - **Quality over popularity:** Content is promoted based on its merit, not the popularity of the author, as all posts are anonmyous. 
#     - **Authentic measurement:** By using quadratic voting Quitter avoids being skewed by a small group of users, while also avoiding the tyranny of the majority.
    
#     #### How does the quadratic voting system work?

#     You get 100 voting 'credits' per round, and you can spend them on any candidate post.
#     The number of votes you give is the square root of the number of credits you spend.
#     This means you can give 1 credit for 1 vote, 4 credits for 2 votes, 9 credits for 3 votes etc.
#     In other words, the marginal cost of adding another vote is 2 more credits than the previous vote.
#     You can also give negative votes to posts you don't like.

#     #### Why does this work?

#     It makes you spend your votes in proportion to how good you think each post is.
#     If you just had 10 votes to spend you would them all on the post you like the most. 
#     Quadratic voting means there are alternatives - you could spend 8 on your favorite and 6 on your second favorite.
#     The tyranny of the majority is also avoided - consider if there were 3 candidates A, B and C.
#     Say 51% of people give A a rating of 10/10, then B 8/10 and C 0/10. 
#     The other 49% give C 10/10 then B 8/10, and A 0/10.
#     In a normal election A would win, as the 51% would give their votes to A.
#     This would not be optimal as 49% of people would be very unhappy.
#     With quadratic voting B would win, as both the 51% and the 49% would give a significant number of votes to B.
#     ''',
#     mathjax=True
# )

explanation1 = html.Div([
    html.P('Welcome to Quitter, a unique social media platform powered by quadratic voting.'),
    html.H4('How does it work?'),
    html.P('Quitter removes the traditional \'like\' system and replaces it with a voting mechanism. '
            'Posts are thinned down in a series of rounds, with a single one being left at the end. '
            'This is done using in a way which incentivises you to vote in accordance with your actual preferences.'),

    html.H4('Why is this a good idea?'),
    html.P('Quitter addresses several issues prevalent in conventional social media platforms:'),
    dcc.Markdown(
        '''
        - **Overwhelming content:** On Quitter only the stuff that matters is makes it, no more reading unfiltered rubbish.
        - **Bias towards frequent users:** On Quitter every user has a fixed influence.
        - **Popularity over quality:** As all posts are anonmyous content is promoted based on its merit, not the popularity of the author.
        - **Tyannies:** Quitter doesn't risk being skewed by a tiny group of users, while also avoiding capture by a majority, thanks to quadratic voting.
        '''
    ),
    html.H4('What is the quadratic voting system?'),
    html.P('You get 100 voting \'credits\' per round, and you can spend them on any candidate post. '
            'The number of votes you give is the square root of the number of credits you spend. '
            'This means you can give 1 credit for 1 vote, 4 credits for 2 votes, 9 credits for 3 votes etc. '
            'In other words, the marginal cost of adding another vote is 2 more credits than the previous vote. '
            'You can also give negative votes to posts you don\'t like.'),
    html.H4('Why does it work?'),
    html.P('It makes you spend your votes in proportion to how good you think each post is. '
            'If you just had 10 votes to spend you would them all on the post you like the most, as every vote makes it slightly more likely to win.'
            'Quadratic voting means there are alternatives - you could spend 8 on your favorite and 6 on your second favorite. '
            'The tyranny of the majority is also avoided - consider if there were 3 candidates A, B and C. '
            'Say 51% of people give A a rating of 10/10, then B 8/10 and C 0/10. '
            'The other 49% give C 10/10 then B 8/10, and A 0/10. '
            'In a normal election A would win, as the 51% would give their votes to A. '
            'This would not be optimal as 49% of people would be very unhappy. '
            'With quadratic voting B would win, as both the 51% and the 49% would give a significant number of votes to B.')
])

explanation2 = dcc.Markdown(
    r'''

    #### Why does it work? - For the mathematically inclined

    Imagine there is an election being run to decide between $n$ candidates. 
    Let the vector $u$ represent the utility you place on each candidate, where $u_i$ is the benefit you get from candidate $i$ winning. 
    We assume that $u$ is normalized such that you expect to get 0 utility from the election without casting a vote. 
    Let $x$ also be a vector of length $n$ where $x_i$ is the number of votes you put towards candidate $i$. 
    You can have negative votes, which count against a candidate. 
    Assuming you don't know how other people have voted, then each vote you cast changes the likelihood of a candidate winning by some probability $p$. 
    If this is the case your utility of voting, $t$, is set $t = p x \cdot u$. 
    This is a plane which intersects at $0$ when $x=\vec{0}$.

    Quadratic voting limits the number of votes you can place by setting the constraint that $\sum_i x_i^2 < c$ for some constant $c$. 
    This effectively means that any rational voter will have $x$ such that it lies in the circle $\sum_i x_i^2 = c$, assuming they don't want to waste votes. 
    The highest $t$ on the plane satisfying this constraint is at $x=\sqrt{c}\frac{u}{|u|}$, meaning you are incentivized to vote exactly in accordance with your normalized utility. 
    To illustrate this we will use a 2D example.

    In the 2D case, the formula for the plane and circle are as follows:

    $$
    \begin{align*}
    t &= x_1 u_1 + x_2 u_2 \\
    c &= x_1^2 + x_2^2
    \end{align*}
    $$

    This is visualized in the figure below. Here $c=100$, and the user has a preference for the second option.
    The black circle is the constraint, and the red line is the constraint mapped onto the plane.
    ''',
    mathjax=True
)

figure1 = html.Div(html.Img(src="/assets/fig_about.png",className="explanation-graph"),className="explanation-graph-container")

explanation3 = dcc.Markdown(
    r'''
    Rearranging the second equation:

    $$
    x_1 = \sqrt{c - x_2^2}
    $$

    Plugging this into the first equation:

    $$
    \begin{align*}
    t &= \sqrt{c - x_2^2} \cdot u_1 + x_2 u_2
    \end{align*}
    $$

    Taking the first derivative with respect to $x_2$:

    $$
    \begin{align*}
    \frac{dt}{dx_2} &= x_2 u_1 \frac{1}{\sqrt{c - x_2^2}} + u_2
    \end{align*}
    $$

    Taking the second derivative with respect to $x_2$:

    $$
    \begin{align*}
    \frac{d^2t}{dx_2^2} &= u_1 c \frac{1}{(c - x_2^2)\sqrt{c - x_2^2}}
    \end{align*}
    $$

    This function is always increasing between $-c$ and $c$. Therefore, the function is concave, and we can set the first derivative to 0 to find the peak.

    Setting the first derivative equal to 0:

    $$
    \begin{align*}
    x_2 u_1 \frac{1}{\sqrt{c - x_2^2}} + u_2 &= 0
    \end{align*}
    $$

    Solving for $x_2$:

    $$
    \begin{align*}
    x_2 u_1 &= -u_2 \sqrt{c - x_2^2} \\
    x_2^2 u_1^2 &= u_2^2 (c - x_2^2) \\
    x_2^2 u_1^2 &= u_2^2 c - u_2^2 x_2^2 \\
    x_2^2 (u_1^2 + u_2^2) &= u_2^2 c \\
    x_2^2 &= c \frac{u_2^2}{u_1^2 + u_2^2} \\
    x_2 &= \sqrt{c} \frac{u_2}{\sqrt{u_1^2 + u_2^2}}
    \end{align*}
    $$

    Effectively, this means $x_2$ is $u_2$ times a constant.
    Pluggin back into equation 2 gives the same for $x_1$.
    For solving in higher dimensions, the same answer can be arrived at using Lagrange multipliers.
    ''',
    mathjax=True
)

explanation4 = dcc.Markdown(
    r'''

    #### This site looks great, but is it built well under the hood?

    No. 

    #### Is there any protection against bots?

    Actually yes, it uses the recaptcha v3 thing from google.

    #### Why did you make this?

    So that I, *Giotto Frean*, can say I did it first, making 2 key innovations:
    
    1. Only letting 1 post get published at a time.
    2. Using quadratic voting on a social media platform.
    
    I hope to appear in some obscure text book in the future, '*The History of Social Media (revised, 2070 edition)*'.

    #### I am Elon Musk and want to buy Quitter for $1 billion. Who do I contact?

    quitterceo@gmail.com

    ''',
    mathjax=True
)

layout = html.Div(
    html.Div(
        [
            logo,
            explanation1,
            explanation2,
            figure1,
            explanation3,
            explanation4
        ],
        className = "explanation-container"
    ),
    className="about-page"
)