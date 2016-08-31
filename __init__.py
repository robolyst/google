# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_, `University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

from web import GenericLogin

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------


class GoogleLogin(GenericLogin):

    def _verify(self, resp):

        # After loging into Google from url_authenticate, I am directed to
        # my account settings page at
        landing_page = 'https://myaccount.google.com/'

        if not resp.url.startswith(landing_page):
            raise Exception("Could not verify that you have successfully logged into Google.")

def login(username, password, disp=False):

    login = GoogleLogin(username,
                     password,
                     url_authenticate = 'https://accounts.google.com/accounts/ServiceLoginAuth',
                     url_login = 'https://accounts.google.com/ServiceLogin',
                     select_form = "@id='gaia_loginform'",
                     username_field = "Email",
                     password_field = "Passwd",
                     disp=disp)

    login.throttle = 1

    return login
