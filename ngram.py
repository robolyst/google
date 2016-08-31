# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

import json
import numpy as np
import pandas as pd
from web import WebAccess, extract

class Ngram(WebAccess):
    """
    Access Google Ngram.
    """

    def fetch_hits(self, content, **kwargs):
        """
        Get the number of times some content appears in books.
        """

        url = "https://books.google.com/ngrams/graph"
        data = {
            'content': content,
            'year_start': 1500,
            'year_end': 2015,
            'corpus': 15,
            'smoothing': 0,
            'share': ''}

        data.update(**kwargs)

        webpage = self.get(url, params=data).text

        extracted_data = extract(webpage, r'var data = (.*?);\n  if ')
        json_data = json.loads(extracted_data)

        extracted_year_range = extract(webpage, r'ngrams.drawD3Chart\((.*?)\);')
        year_range = extracted_year_range.split(', ')[1:3]

        years = [int(y) for y in year_range]

        df = pd.DataFrame() #pylint: disable=C0103
        for ngram in json_data:
            df[ngram['ngram']] = ngram['timeseries']

        df['year'] = np.arange(years[0], years[1]+1, 1)

        df.index = df.year
        del df['year']

        return df

# pylint: disable=R0903
class WordFreq(object):
    """
    Old code for handling word frequency files. This should be deprecated.
    """

    def __init__(self, fname):
        self.fname = fname
        self.data = {}
        self.total_count = np.nan

        self._load()

    def __getitem__(self, key):
        return self.data[key] / self.total_count

    def _load(self):

        self.data = {}

        with open(self.fname, 'r') as filehandle:

            for line in filehandle:

                line = line.strip("\n").split('\t')
                ngram = line[0]
                count = float(line[1])

                ngram = ngram.lower()

                if ngram in self.data:
                    self.data[ngram] += count
                else:
                    self.data[ngram] = count

        self.total_count = float(np.sum(self.data.values()))
