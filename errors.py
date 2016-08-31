# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Thu Nov 13 09:55:07 2014
"""


class ExceededQuotaException(Exception):
    """
    Exception for when Google returns the message "You have exceeded your
    quota."
    """
    pass

def handle_HTTPError(error):

    data = {
        'code': error.code,
        'url': error.geturl(),
        'reason': error.reason,
    }

    message = """HTTP Error %(code)d
    URL: %(url)s
    Reason: %(reason)s""" % data

    error.message = message

    print message
    raise error
