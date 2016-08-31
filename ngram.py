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


class Ngram(WebAccess):

    def fetch_hits(self, content, **kwargs):

        url = "https://books.google.com/ngrams/graph"
        data = {'content': content, 'year_start': 1500, 'year_end': 2015, 'corpus': 15, 'smoothing': 0, 'share': ''}

        data.update(**kwargs)

        webpage = self.get(url, params=data).text

        extracted_data = extract(webpage, r'var data = (.*?);\n  if ')
        json_data = json.loads(extracted_data)

        v = extract(webpage, r'ngrams.drawD3Chart\((.*?)\);')
        year_range = v.split(', ')[1:3]

        years = [int(y) for y in year_range]

        df = pd.DataFrame()
        for ngram in json_data:
            df[ngram['ngram']] = ngram['timeseries']

        df['year'] = np.arange(years[0], years[1]+1, 1)

        df.index = df.year
        del df['year']

        return df


class WordFreq(object):

    def __init__(self, fname):
        self.fname = fname
        self.DATA = {}
        self.total_count = np.nan

        self._load()

    def __getitem__(self, key):
        return self.DATA[key] / self.total_count

    def _load(self):

        self.DATA = {}

        with open(self.fname, 'r') as file:

            for line in file:

                line = line.strip("\n").split('\t')
                ngram = line[0]
                count = float(line[1])

                ngram = ngram.lower()

                if ngram in self.DATA:
                    self.DATA[ngram] += count
                else:
                    self.DATA[ngram] = count

        self.total_count = float(np.sum(self.DATA.values()))
