# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_, `University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

import httplib
import urllib
import urllib2
from re import search, DOTALL
import csv
import lxml.etree as etree
import lxml.html as html
import traceback
import gzip
import random

import time
import sys
from datetime import datetime
import numpy
import json
import numpy as np
from copy import copy

from StringIO import StringIO
import pandas as pd

import hashlib

import pytree.misc

from web import GenericLogin, WebAccess, extract, find_html_elements, search_html

from nltk import clean_html


class Hits(WebAccess):

    search_url  = 'https://www.google.com/search'

    def __init__(self, http_access):

        self.http_access = http_access
        self.fetch_data = self.http_access.fetch_data


    def _fetch_single_hits(self, searchfor):

        args = {
        'q': searchfor,
        'newwindow': 1,
        }

        search_results = self.http_access.fetch_data(self.search_url, args)

        count = extract(search_results, r'About (.*?) results')

        count = float(count.strip(' ').replace(',', ''))

        return count

    def fetch_hits(self, searchfor):

        terms = searchfor

        if type(terms) is str:
            terms = terms.split(',')

        search_terms = ['"%s"' % s if len(s.split(' ')) > 1 else s for s in terms]

        results = [self._fetch_single_hits(s) for s in search_terms]

        df = pd.DataFrame()
        df['terms'] = terms
        df['hits'] = results

        return df
