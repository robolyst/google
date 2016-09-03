# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

import urllib
from datetime import datetime
import json
import numpy as np
from copy import copy
from StringIO import StringIO
import pandas as pd
from web import extract, find_html_elements, search_html
from nltk import clean_html

class Trends(object):


    def __init__(self, google_login):

        super(Trends, self).__init__()

        self.http_access = google_login
        self.get = self.http_access.get
        self.post = self.http_access.post

        #self.url = 'http://www.google.com/trends/trendsReport'
        self.url = 'http://www.google.com/trends/trendsReport'

    def _query_sanity_check(self, query=[], country=[], **kwargs):

        # Sanity checking
        if type(query) != list or type(country) != list:
            raise Exception('query and country must be lists.')

        if len(country) > 1:
            if len(query) > 1:
                raise Exception('Can have multiple search terms OR multiple countries, but not both.')

    def build_trends_request(self, **kwargs):
        """
        Parameters:
        q (string or array) - The search term(s) to return.
        geo (string or array) - The country or countries from which users are
            searching for the search terms.
        """

        params = {
                'export': 1,
                'hl': 'en-US',
                'geo': 'us'
                }

        params.update(kwargs)

        # Prepare inputs
        # query and country can be either an array or a csv string
        if type(params['q']) is str or type(params['q']) is unicode:
            params['q'] = params['q'].split(',')

        if type(params['geo']) is str or type(params['geo']) is unicode:
            params['geo'] = params['geo'].split(',')


        # Convert the date field if provided as a datetime object
        if "date" in params and type(params["date"]) is datetime:
            params["date"] = params["date"].strftime("%Y-%m-%dT%H\:%M\:%S 24H")


        if len(params['geo']) > 1:
            params['cmpt'] = 'geo'
        else:
            params['cmpt'] = 'q'

        if len(params['q']) > 0:
            params['q'] = ','.join(params['q'])

        if len(params['geo']) > 0:
            params['geo'] = ','.join(params['geo'])

        print self.url + "?" + urllib.urlencode(params)

        return self.url, params

    def _get_category_list(self):

        data = self.web.fetch_data('http://www.google.com/trends/explore')

        cat_json = extract(data, r'trends.Category.setTreeData\((.*?)\);\n')

        data = json.loads(cat_json)

        IDS = []
        names = []

        id =[]

        def p(data, id):

            id.append(data['id'])

            IDS.append(copy(id))
            names.append(data['name'])

            if 'children' in data:
                for kid in data['children']:
                    id = p(kid, id)

            id = id[:-1]

            return id

        p(data, id)

        return IDS, names

    def fetch_trends_csv(self, usebrowser=False, browser_timeout=60, display=False, **kwargs):
        """
        Get a Google Trends CSV file
        """

        url, params = self.build_trends_request(**kwargs)

        if display:
            print url
            print params
            print url + "?" + urllib.urlencode(params)

        if usebrowser:
            data = self.fetch_data_wb(self.url, params, fname='report.csv', timeout=browser_timeout)
        else:
            data = self.get(self.url, params=params).text

        if '<!DOCTYPE html><html ><head>' in data:
            raise Exception('Google did not return a csv file\n\n' + clean_html(data))

        return data

    @staticmethod
    def _extract_trend_series_from_csv(data):

        trend_data = extract(data, r'Interest over time(.*?)(\n\n\n)')

        df = pd.read_csv(StringIO(trend_data), delimiter=',')

        # Convert all the search trends to floads
        for search_term in df.columns[1:]:

            is_percent = (type(df[search_term][0]) is str) and df[search_term][0].endswith('%')

            if is_percent:
                for i in range(len(df)):
                    if df[search_term][i].strip(' ') == '':
                        df[search_term][i] = np.nan
                    else:
                        df[search_term][i] = float(df[search_term][i].strip('%'))/100.0

            df[search_term] = df[search_term].convert_objects(convert_numeric=True)

        # Split the week field into start and end
        if "Week" in df.columns:
            start = [item.split(' - ')[0] for item in df['Week']]
            end = [item.split(' - ')[1] for item in df['Week']]
            df['start'] = start
            df['end'] = end
            del df['Week']

            df.start = pd.to_datetime(df.start)
            df.end = pd.to_datetime(df.end)


        def str_2_datetime(s):

            if "UTC" in s:
                return datetime.strptime(t, "%Y-%m-%d-%H:%M UTC")
            else:
                return datetime.strptime(t, "%Y-%m-%d-%H:%M")

        # Convert the time field
        if "Time" in df.columns:
            dates = [str_2_datetime(t) for t in df.Time]
            df["Time"] = dates


        return df


    def entity_query(self, name):

        url = 'http://www.google.com/trends/entitiesQuery'
        params = {
            "q": name,
            "tn": 4
        }

        result = self.get(url, params=params)

        data = json.loads(result.text)["entityList"]

        return data

    def fetch_trends(self, compare=True, usebrowser=False, **kwargs):


        if compare:

            data = self.fetch_trends_csv(usebrowser=usebrowser, **kwargs)

            return self._extract_trend_series_from_csv(data)

        else:

            res = []

            for q in query:
                for geo in country:

                    data = self.fetch_trends_csv(q, country=geo, usebrowser=usebrowser, **kwargs)

                    try:
                        res.append(self._extract_trend_series_from_csv(data))
                    except Exception, e:
                        print e.message
                        print q, geo


            result = res[0]
            for r in res[1:]:
                result = result.merge(r)

            return result


def overlap(left, right):
    """
    Calculate the overlap between the left and right side.

    Returns None if no overlap exists.
    """
    for i in range(len(left)):

        sleft = left.iloc[-i:, :]
        sright = right.iloc[:i, :]

        # Check to make sure they line up
        match = np.sum(~(sleft.Time.values == sright.Time.values)) == 0

        if match:
            return i

    return None


def add_intercept(vector):
    return np.append(vector.flatten()[:, np.newaxis], np.ones(len(vector))[:, np.newaxis], 1)

def stich(left, right):
    """
    Joins two time series with an overlap and assumes that they have been
    linearly scaled to two different scales.

    Assumes that left and right are pandas data frames with two colummns. The
    first column should be labled "Time" and should be a datetime column.
    """

    cut = overlap(left, right)

    if cut is None:
        raise Exception("Cannot line up time series.")

    sleft = left.iloc[-cut:, :]
    sright = right.iloc[:cut, :]

    # Check to make sure they line up
    match = np.sum(~(sleft.Time.values == sright.Time.values)) == 0

    if not match:
        print sleft
        print sright
        raise Exception("The time series do not line up.")


    # Step 1: linearly scale the left side to line up with the right side

    # get the left and right values
    left_values = sleft.iloc[:, 1].values
    right_values = sright.iloc[:, 1].values

    left_change = np.mean(np.abs(np.diff(left_values)))
    right_change = np.mean(np.abs(np.diff(right_values)))

    # Calculate the weights to scale the left side to match the right side

    # scale to match the right side
    if right_change >= left_change:
        x = np.linalg.lstsq(add_intercept(left_values), right_values)[0]
    # scale the right side to match the left then convert the weights to
    # scale the left side.
    else:
        x = np.linalg.lstsq(add_intercept(right_values), left_values)[0]
        x[1] = -x[1] / x[0]
        x[0] = 1/x[0]

    # Convert the left side
    c_left = left.iloc[:, 1].values
    c_left = np.append(c_left[:, np.newaxis], np.ones(len(c_left))[:, np.newaxis], 1)
    c_left = np.dot(c_left, x)

    # Put back into the left side
    sleft.iloc[:, 1] = np.dot(add_intercept(left_values), x)
    left.iloc[:, 1] = c_left

    # Step 2: Linearly fade between the two sides

    l = sleft.iloc[:, 1].values
    r = sright.iloc[:, 1].values
    a = np.linspace(1, 0, len(l))

    fade = sleft.copy()
    fade.iloc[:, 1] = l*a + r*(1-a)

    # Join everything together

    right = fade.append(right.iloc[cut:, :])
    right = left.iloc[:-cut, :].append(right)

    return right
