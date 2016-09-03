import google


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

def test_google_login():
    account = google.Session("robsmseghthwne@gmail.com", "anog0j4h")
