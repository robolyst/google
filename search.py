# -*- coding: utf-8 -*-
"""
:Author: `Adrian Letchford <http://www.dradrian.com>`_
:Organisation: `Warwick Business School <http://www.wbs.ac.uk/>`_,
`University of Warwick <http://www.warwick.ac.uk/>`_.
:Created On: Tue May 06 13:31:45 2014
"""

from web import WebAccess, find_html_elements


class Search(WebAccess):
    """
    Access Google's search engine.
    """

    search_url = 'https://www.google.com/search'

    def __init__(self, http_access):
        super(Search, self).__init__()
        self.http_access = http_access
        self.fetch_data = self.http_access.fetch_data


    def _fetch_search_page(self, searchfor, page=1, **kwargs):

        args = {
            'q': searchfor,
            'newwindow': 1,
            'start' : (page - 1) * 10
        }

        args.update(**kwargs)

        search_results = self.fetch_data(self.search_url, args)

        return search_results

    @staticmethod
    def _scrape_results(search_page):

        search_results = []

        search_reg = "//li[contains(@class, 'g')]"
        for result in find_html_elements(search_page, search_reg):

            try:

                header = result.find_class('r')[0].find('.//a')
                url = header.attrib['href']
                title = header.text_content()

                info_box = result.find(".//span[@class='st']")
                blurb = info_box.text_content()

                search_results.append({
                    'title': title,
                    'url': url,
                    'blurb': blurb,
                })

            except Exception: #pylint: disable=W0703
                pass

        return search_results
