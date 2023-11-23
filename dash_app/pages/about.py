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

dash.register_page(__name__,path="/about", title="About")

logo = html.Div(html.Img(src="/assets/logo.svg",className="logo-about"), className="logo-about-container")

explanation1 = html.Div([
    html.P('Welcome to Quitter, a unique social media platform powered by quadratic voting.'),
    html.H4('How does it work?'),
    html.P('Quitter removes the traditional \'like\' system and replaces it with a voting mechanism. '
            'Posts are thinned down in a series of rounds, with a single one being left at the end. '
            'This is done using in a way which incentivises you to vote in accordance with your actual preferences.'),

    html.H4('Why is this a good idea?'),
    html.P('Quitter addresses several issues prevalent in conventional social media platforms:'),
    html.Ul([
        html.Li([
            html.Strong("Overwhelming content:"),
            " On Quitter only the stuff that matters makes it, no more reading unfiltered rubbish."
        ]),
        html.Li([
            html.Strong("Bias towards frequent users:"),
            " On Quitter every user has a fixed influence in the voting process. Other platforms let users like as much as they want."
        ]),
        html.Li([
            html.Strong("Popularity over quality:"),
            " As all posts are anonymous, content is promoted based on its merit, not the popularity of the author."
        ]),
        html.Li([
            html.Strong("Tyrannies:"),
            " Quitter doesn't risk being skewed by a tiny group of users, while also avoiding capture by a majority, thanks to quadratic voting."
        ])
    ]),
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
    
    #### Do all users see the same posts?

    Only in the final round.
    In other rounds the posts you see are randomly selected.
    Votes are then normalised by the number of people who saw the post.
    
    #### This site looks great, but is it built well under the hood?

    No. 

    #### Is there any protection against bots?

    Actually yes, it uses the recaptcha v3 thing from google.

    #### Why did you make this?

    So that I, *Giotto Frean*, can say I did it first, and maybe appear in some obscure text book in the future, '*The History of Social Media (revised, 2070 edition)*'.

    #### Is there some source code somewhere?

    Yes, it's on github [here](https://github.com/GiottoFrean/Quitter)

    #### I am Elon Musk and want to buy Quitter for $1 billion. Who do I contact?

    quitterceo@gmail.com

    ''',
    mathjax=True
)

explanation3 = dcc.Markdown(
    r'''

    #### Why does it work? - For the mathematically inclined

    Imagine there is an election being run to decide between $n$ candidates.
    Say you don't really know how other people will vote.
    Then each vote you cast for a candidate $i$ has a fixed utility - a slightly higher chance of that candidate winning.
    Let the vector $u$ represent those utilities, with $u_i$ being the utility of voting for candidate $i$.
    $u$ is proportionate to the (relative) benefit you would get from each candidate winning. 
    Let $x$ also be a vector of length $n$ where $x_i$ is the number of votes you put towards candidate $i$.
    You can vote multiple times and have negative votes, which count against a candidate. 
    Your marginal utility of voting, $t$, is then set $t = x \cdot u$. 
    This is a plane which intersects at $0$ when $x=\vec{0}$.

    Quadratic voting limits the number of votes you can place by setting the constraint that $\sum_i x_i^2 < c$ for some constant $c$. 
    This effectively means that any rational voter will have $x$ such that it lies in the circle $\sum_i x_i^2 = c$, given they don't want to waste votes. 
    The highest $t$ on the plane satisfying this constraint is at $x=\sqrt{c}\dfrac{u}{\|u\|}$.
    
    This means you are incentivized to vote exactly in accordance with your normalized utility. 
    To illustrate this we will look at a 2D example.

    In the 2D case, the formula for the plane and circle are as follows:

    $$
    \begin{align*}
    t &= x_1 u_1 + x_2 u_2 \\
    c &= x_1^2 + x_2^2
    \end{align*}
    $$

    An example is visualized in the figure below. Here $c=100$, and the user has a preference for the second option.
    The black circle is the constraint, and the red line is the constraint mapped onto the plane.
    ''',
    mathjax=True
)

figure1 = html.Div(html.Img(src="/assets/fig_about.png",className="explanation-graph"),className="explanation-graph-container")

explanation4 = dcc.Markdown(
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
    Plugging back into equation 2 gives the same for $x_1$.
    For solving in higher dimensions, the same answer can be arrived at using Lagrange multipliers.

    *Note 1: 
    This logic doesn't hold if you drop the assumption that you don't know how other people will vote. 
    If you know nobody else will vote for a candidate, you will still have an incentive not vote for them either.
    A possible fix is to use randomness to make it so that each vote for a candidate increases the chance of that candidate winning very slightly, but that isn't implemented on this site.*
    
    *Note 2:
    The 'relative' beneftis of each candidate winning are not exactly the same as the 'absolute' benefits.
    If you rate candidate A 10/10 and candidate B 8/10 then the relative benefit of A winning to you is 1/10 and the relative benefit of B winning is -1/10.
    The same is true if you rate A 2/10 and B 0/10.*

    *Note 3:
    This doesn't account for candidates having different total utilities.
    Someone who rates A 10/10 and B 9/10 has the same number of credits as someone who rates A 10/10 and B 0/10.
    The only way around that problem is to make users pay in an actual currency for their votes, which adds a number of other issues.*
    ''',
    mathjax=True
)


layout = html.Div(
    html.Div(
        [
            logo,
            explanation1,
            explanation2,
            explanation3,
            figure1,
            explanation4
        ],
        className = "explanation-container"
    ),
    className="about-page"
)