# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Sat May 31 17:25:53 2014
"""
# pylint: disable=E1101

from re import search, DOTALL
import gzip
from StringIO import StringIO
import urllib
import socket
import random
import time
import getpass
import platform
import os
import lxml.etree as etree
import lxml.html as html
import traceback
import requests
import webbrowser

def my_ip():
    """Returns the IP of this computer."""
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.connect(('google.com', 0))
    return soc.getsockname()[0]


def get_data_from_response(resp):
    """
    Get the data from a requests response and decompress it if necessary.
    """
    if resp.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(resp.read())
        virtualfile = gzip.GzipFile(fileobj=buf)
        data = virtualfile.read()
    else:
        data = resp.read()

    return data

def make_url(url, data):
    """Encode a dictionary onto the end of a URL."""
    encoded_data = urllib.urlencode(data)
    url += '?' + encoded_data
    return url

def encoded_dict(in_dict):
    """Clean up a dictionary's string encoding."""
    # pylint: disable=C0103
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

def get_downloads_loc():
    """Get the system's default download directory."""

    system = platform.system()
    release = platform.release()

    loc = None

    if system == 'Windows' and release == '7':

        loc = u'D:/settings/%s/Downloads/' % (getpass.getuser())

    if system == 'Linux':

        loc = u'/home/%s/Downloads/' % (getpass.getuser())

    if loc is None:

        print system
        print release

        raise Exception('Could not identify system: %s : %s' % (system, release))

    return loc

def can_modify_file(filename):
    """Returns true if the file can be modified."""
    if not os.path.isfile(filename):
        return False
    try:
        return bool(open(filename, 'a', 8))
    except: # pylint: disable=W0702
        return False


def extract(data, reg):
    """
    Extract string with a regular expression.
    """

    result = search(reg, data, DOTALL)

    if result:
        result = result.group(1)
    else:
        raise Exception("Could not extract data.")

    result = result.strip('\n')

    return result


def prepare_url(url, data, is_unicode=False):
    """
    Joins a dictionary of data onto a url.
    """

    if is_unicode:
        data = encoded_dict(data)

    encoded_data = None
    if data is not None:
        encoded_data = urllib.urlencode(data)

    full_url = url
    if encoded_data is not None:
        full_url += '?' + encoded_data

    return full_url, encoded_data, data

def find_html_elements(data, reg):
    """
    Extracts HTML elements from a blob of HTML.
    """

    find_elements = etree.XPath(reg, regexp=True)
    tree = etree.fromstring(data, parser=html.HTMLParser(recover=True, remove_comments=True))
    return find_elements(tree)


def search_html(data, reg): # pylint: disable=W0613
    """Deprecated. Use `find_html_elements`."""
    raise Exception("This function is deprecated. Use find_html_elements.")



class WebAccess(requests.Session):
    """
    Wrapper around a requests Session that adds throttling and downloading a
    datafile through a browser.
    """

    def __init__(self):
        super(WebAccess, self).__init__()

        self.throttle = None

    def wait_throttle(self):
        """
        Sleep for the throttle duration.
        """
        # Randomized download delay
        if self.throttle is not None:
            r = random.uniform(0.5 * self.throttle, 1.5 * self.throttle)
            print "Throttle, sleeping for:", r
            time.sleep(r)

    def get(self, *args, **kwargs):
        self.wait_throttle()
        return super(WebAccess, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.wait_throttle()
        return super(WebAccess, self).post(*args, **kwargs)


    def fetch_data_wb(self, url, data=None, fname=None, is_unicode=False, timeout=60):

        if fname is None:
            raise NotImplementedError("The capability to read a web page's \\\
                source is not yet built in.")

        fname = get_downloads_loc() + fname

        GET_url, encoded_data, data = prepare_url(url, data, is_unicode)

        # Make sure the file doesn't exist
        if os.path.isfile(fname):
            os.remove(fname)

        # Open web page
        webbrowser.open(GET_url, new=0, autoraise=False)

        # Wait for file to download
        seconds_asleep = 0
        while not can_modify_file(fname):

            time.sleep(1)
            seconds_asleep += 1

            if seconds_asleep >= timeout:
                raise IOError("File did not download in %d seconds" % timeout)

        # Open file
        with open(fname, 'r') as file:
            web_data = file.read()

        # Return file
        return web_data


class AuthWebSession(WebAccess):
    """
    A requests Session that logs in through a web interface.
    """

    def __init__(self, username, password, url_authenticate, url_login,
                 select_form, username_field, password_field, disp=False):

        super(AuthWebSession, self).__init__()

        self.login_params = {}

        self.url_authenticate = url_authenticate
        self.url_login = url_login
        self.select_form = select_form
        self.username_field = username_field
        self.password_field = password_field

        self.disp = disp

        self._authenticate(username, password)

    def _log(self, message):
        if self.disp:
            print message

    def _authenticate(self, username, password):

        # Get all of the login form input values
        find_inputs = etree.XPath("//form[%s]//input" % self.select_form)

        try:

            self._log("Sending GET request to: %s" % self.url_login)

            resp = self.get(self.url_login)
            data = resp.text

            #self._log("Retrieved dat:\n%s" % BeautifulSoup(data).get_text())

            if self.disp:
                print "Got login page."

            parser = html.HTMLParser(recover=True, remove_comments=True)
            xmlTree = etree.fromstring(data, parser=parser)

            for input in find_inputs(xmlTree):
                name = input.get('name')
                if name:
                    name = name.encode('utf8')
                    value = input.get('value', '').encode('utf8')
                    self.login_params[name] = value
        except: # pylint: disable=W0702
            print "Exception while parsing: %s\n" % traceback.format_exc()

        self.login_params[self.username_field] = username
        self.login_params[self.password_field] = password

        resp = self.post(self.url_authenticate, params=self.login_params)

        self._verify(resp)

    def _verify(self, resp):
        pass
