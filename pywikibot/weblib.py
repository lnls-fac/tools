# -*- coding: utf-8  -*-
"""
Functions for manipulating external links
or querying third-party sites.

"""
#
# (C) Pywikibot team, 2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: 017965a14137eda197a60436ad95b5ebe5dc09c7 $'

import urllib
from pywikibot.comms import http


def getInternetArchiveURL(url, timestamp=None):
    """Return archived URL by Internet Archive.

    Parameters:
        url - url to search an archived version for
        timestamp - requested archive date. The version closest to that moment
                    is returned. Format: YYYYMMDDhhmmss or part thereof.

    See [[:mw:Archived Pages]] and https://archive.org/help/wayback_api.php
    for more details.
    """
    import json
    uri = u'https://archive.org/wayback/available?'

    query = {'url': url}

    if timestamp is not None:
        query['timestamp'] = timestamp

    uri = uri + urllib.urlencode(query)
    jsontext = http.request(uri=uri, site=None)
    if "closest" in jsontext:
        data = json.loads(jsontext)
        return data['archived_snapshots']['closest']['url']
    else:
        return None


def getWebCitationURL(url, timestamp=None):
    """Return archived URL by Web Citation.

    Parameters:
        url - url to search an archived version for
        timestamp - requested archive date. The version closest to that moment
                    is returned. Format: YYYYMMDDhhmmss or part thereof.

    See http://www.webcitation.org/doc/WebCiteBestPracticesGuide.pdf
    for more details
    """
    import xml.etree.ElementTree as ET
    uri = u'http://www.webcitation.org/query?'

    query = {'returnxml': 'true',
             'url': url}

    if timestamp is not None:
        query['date'] = timestamp

    uri = uri + urllib.urlencode(query)
    xmltext = http.request(uri=uri, site=None)
    if "success" in xmltext:
        data = ET.fromstring(xmltext)
        return data.find('.//webcite_url').text
    else:
        return None
