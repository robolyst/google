# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014

TODO: Merge this with Search.
"""

import pandas as pd
from web import WebAccess, extract

class Hits(WebAccess):
    """
    Get's the search results hits on Google searches.
    """

    search_url = 'https://www.google.com/search'

    def __init__(self, http_access):

        super(Hits, self).__init__()

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
        """
        Fetches the number of Google search results for a query.
        """

        terms = searchfor

        if type(terms) is str: # pylint: disable=C0123
            terms = terms.split(',')

        search_terms = ['"%s"' % s if len(s.split(' ')) > 1 else s for s in terms]

        results = [self._fetch_single_hits(s) for s in search_terms]

        data = pd.DataFrame()
        data['terms'] = terms
        data['hits'] = results

        return data
