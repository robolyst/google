# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Created On: Tue May 06 13:31:45 2014
"""

from web import AuthWebSession

class UnverifiedLoginException(Exception):
    """
    Exception for when we could not verify that we've logged into Google."
    """
    pass

class Session(AuthWebSession):
    """
    A requests Session that is logged into Google's services.
    """

    def __init__(self, username, password, disp=False):

        url_auth = 'https://accounts.google.com/accounts/ServiceLoginAuth'
        url_login = 'https://accounts.google.com/ServiceLogin'

        super(Session, self).__init__(username,
                                      password,
                                      url_authenticate=url_auth,
                                      url_login=url_login,
                                      select_form="@id='gaia_loginform'",
                                      username_field="Email",
                                      password_field="Passwd",
                                      disp=disp)

    def _verify(self, resp):
        """
        Called by the parent class to verify that we have successfully logged
        in. If the login is unable to be verified a `UnverifiedLoginException`
        will be raised.
        """
        # After loging into Google from url_authenticate, I am directed to
        # my account settings page at
        landing_page = 'https://myaccount.google.com/'

        if not resp.url.startswith(landing_page):
            raise UnverifiedLoginException()
