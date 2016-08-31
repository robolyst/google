# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_, `University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

# Built in imports
import lxml.etree as etree
import lxml.html as html
from StringIO import StringIO
import hashlib
from urllib2 import HTTPError
import os

# External imports
import pandas as pd
from nltk import clean_html
from requests import Timeout
import numpy as np

# Internal imports
from web import WebAccess, extract, search_html
from errors import handle_HTTPError


def pd_to_csv(df, **kwargs):
    """
    Takes a :class:`pandas.DataFrame` and returns a csv.
    """
    a = StringIO()
    df.to_csv(a, **kwargs)
    a.pos = 0
    return a.read()


class Correlate(WebAccess):
    """
    Fetches Google Correlate results.

    To get the Google Correlate results page for state data, follow these steps:

    * Post the following parameters to http://www.google.com/trends/correlate/upload:
        * t = 'all'
        * p = ''
        * e = the name of your data file
        * csv = the csv file (as text) of your data
        * xsrf = some security code that google added during 2014 Christmas

    """

    def __init__(self, http_access):
        self.http_access = http_access
        self.get = self.http_access.get
        self.post = self.http_access.post

        self.upload_url = 'http://www.google.com/trends/correlate/upload'
        self.search_url = 'http://www.google.com/trends/correlate/search'
        self.dash_url = 'http://www.google.com/trends/correlate/dashboard'

        self.last_search = None

        self.xsrf = None
        self.xsrf_usage_count = 0


        # If we're searching by US states
        # t = all
        # p = blank

        # If we're searching by time
        # t = weekly, monthly
        # p = two letter country code, lowercase

    #==========================================================================
    # getter functions (very javaesque)
    #==========================================================================

    def get_xsrf(self):

        if self.xsrf is None or self.xsrf_usage_count >= 50:
            resp = self.get('http://www.google.com/trends/correlate/edit?e=&t=weekly')
            regex = "//input[@name='xsrf']"
            try:
                self.xsrf = search_html(resp.text, regex)[0].value

            except:
                raise Exception("Couldn't get the xsrf code from Google.")

            self.xsrf_usage_count = 0

        self.xsrf_usage_count += 1
        return self.xsrf

    #==========================================================================
    # Utility Functions
    #==========================================================================

    def _get_correlate_webpage(self, data, time = 'all', country = '', **kwargs):

        #------------------------------
        # Make query aruments
        #------------------------------
        args = {
        't': time,
        'p': country,
        }
        args.update(**kwargs)


        #------------------------------
        # Convert data to args
        #------------------------------

        # If the data is a CSV string
        if type(data) is str and '\n' in data:

            args.update({
                'e' : hashlib.md5(data).hexdigest(), # CSV file name
                'csv': data,
                })

        # data is a google trends search term
        elif type(data) is str:

            args.update({
                'e' : data.replace(' ', '+'),
                })


        # Data comes from pandas
        elif type(data) is pd.DataFrame or type(data) is pd.Series:

            mydata = data

            if time == 'monthly':
                mydata = mydata.resample('MS')
            if time == 'weekly':
                mydata = mydata.resample('W-SAT')

            mycsv = pd_to_csv(mydata, header=False)

            args.update({
                'e' : hashlib.md5(mycsv).hexdigest(), # CSV file name
                'csv': mycsv,
                })

        else:
            raise Exception("Don't recognise the query type.")

        #------------------------------
        # Grab the data
        #------------------------------

        if 'csv' not in args:
            # if this is a general search
            webpage = self.get(self.search_url, params=args)
        else:
            args['xsrf'] = self.get_xsrf()
            webpage = self.post(self.upload_url, data=args)

        if webpage.status_code != 200:

            print "-"*80
            print "Error talking to Google"
            print "Status code:", webpage.status_code
            print webpage.content

            print "Google's reply:", clean_html(webpage.content)

            print "-"*80
            raise Exception("eek!")

        return webpage.text


    def _scrape_correlations(self, webpage):

        regex = "//li[@class='result' or (@class='result selected')]"

        corr = []
        terms = []
        for input in search_html(webpage, regex):

            corr.append(float(input.find('small').text))

            if input.find('a') == None:
                terms.append(input.find('span').text)
            else:
                terms.append(input.find('a').text)

        Correlation = pd.core.frame.DataFrame({
            'Term': terms,
            'Correlation': corr,
        })

        return Correlation

    def _scrape_timeseries_url(self, webpage):

        extracted = extract(webpage, r'Export data as (.*?)CSV</a>')
        extracted = extract(extracted, r'\"(.*?)\"')

        csv_url = 'http://www.google.com' + extracted

        return csv_url


    #==========================================================================
    # Main functions
    #==========================================================================


    def search(self, data, time='all', country='', **kwargs):

        webpage = self._get_correlate_webpage(data, time, country, **kwargs)

        self.last_search = webpage

        correlations = self._scrape_correlations(webpage)

        return correlations

    def get_series(self):

        if self.last_search == None:
            raise Exception("You must call search() first.")

        csv_url = self._scrape_timeseries_url(self.last_search)

        try:

             # Retrieve the csv data from google correlate
            csv_data = self.get(csv_url)

        except HTTPError, error:
            handle_HTTPError(error)

        # Process the downloaded CSV file
        series = pd.read_csv(StringIO(csv_data), skiprows=11)

        series.index = pd.to_datetime(series.Date)
        del series['Date']

        return series


    def delete_all_files(self):
        """
        Deletes all the files from the user's Google Correlate dashboard.
        """
        #webpage = self.get_webpage(self.dash_url, opener=self.http_access.opener, cache=False)
        resp = self.get(self.dash_url)

        webpage = resp.text

        print "status code:", resp.status_code
        print "size:", len(webpage)


        find_inputs = etree.XPath("//tr//input[@type='hidden']", regexp=True)
        xmlTree = etree.fromstring(webpage, parser=html.HTMLParser(recover=True, remove_comments=True))

        inputs = find_inputs(xmlTree)

        if len(inputs) % 2 != 0:
            raise Exception('Problem scraping correlate dashboard')

        for i in range(len(inputs) / 2):
            elements = inputs[i*2:i*2+2]

            data = {}

            for e in elements:
                data[e.name] = e.value

            try:
                # Get the correlate webpage
                webpage = self.post(self.dash_url, data=data, timeout=2)
            except Timeout:
                pass

            print "deleting file", i, "of", len(inputs) / 2

    def search_batch(self, input_data, fname, *args, **kwargs):

        # Open or create the dump file
        if os.path.isfile(fname):
            google_results = pd.read_csv(fname, index_col=0)
        else:
            google_results = pd.DataFrame()

        # Calculate which dataset to start from
        start = 0
        try:
            start = max(google_results.series.values) + 1
        except:
            pass
        start = int(start)

        # Loop through the input datasets
        for i in range(start, np.shape(input_data)[1]):

            results = pd.DataFrame(index = range(100))
            results['k'] = results.index

            series = input_data.iloc[:, i]

            try:
                retrieved = self.search(series, *args, **kwargs)
            except:
                print "Kicked off Google!!!"
                break

            results = results.merge(retrieved, how='outer', left_index=True, right_index=True)
            results['series'] = i

            google_results = google_results.append(results)

            if len(retrieved) > 0:
                print "Dataset %d : Google search terms %d : top term '%s' @ %0.4f" % (i, len(retrieved), results.Term.values[0], results.Correlation.values[0])
            else:
                print "Dataset %d : Google search terms %d" % (i, len(retrieved))

            # Save every 10 just incase something goes wrong!
            #if i % 10 == 0:
            google_results.to_csv(fname)

        # Do a final save
        google_results.to_csv(fname)
