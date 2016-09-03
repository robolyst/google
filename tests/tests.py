# pylint: disable=E0401,C0111,W0603
import pandas as pd

import google
import google.trends

"""
Test google account

First name: Python
Last name: Package
email: robsmseghthwne@gmail.com
password: anog0j4h
Birthday: April 02 1985
Gender: Male
Location: Australia
"""

SESSION = None

def get_session():
    global SESSION
    if SESSION is None:
        SESSION = google.Session("robsmseghthwne@gmail.com", "anog0j4h")
    return SESSION

def test_get_session():
    assert isinstance(get_session(), google.Session)

def test_google_login():
    get_session()

def test_trends_fetch():

    session = get_session()
    trends = google.trends.Trends(session)
    data = trends.fetch_trends(q="Linus")

    assert isinstance(data, pd.DataFrame)
    assert len(data) > 500
