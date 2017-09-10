# -*- coding: utf-8 -*-

"""
    G2 Add-on Package
    Thanks to NeverWise
    Copyright (C) 2016 J0rdyZ65

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import urllib
import urlparse

from g2.libraries import log
from g2.libraries import client


info = {
    # (fixme) the 2nd domains is needed for an issue in resolvers._top_domain.
    'domains': ['rai.it', 'www.rai.it'],
}

_BASE_URL = "http://www.rai.it"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2956.0 Safari/537.36"


def resolve(dummy_module, url):
    log.debug('{m}.{f}: URL: %s', url)
    url = _fetch_url(url)

    if url.startswith('http://mediapolis.rai.it/relinker/relinkerServlet.htm') or \
       url.startswith('http://mediapolisvod.rai.it/relinker/relinkerServlet.htm') or \
       url.startswith('http://mediapolisevent.rai.it/relinker/relinkerServlet.htm'):
        log.debug('{m}.{f}: Relinker URL: %s', url)
        url = _relinker(url)

    log.debug('{m}.{f}: Resolved URL: %s', url)
    return url


def _fetch_url(url):
    with client.Session() as session:
        video = session.get(url).json()
        if not video.get('pathFirstItem'):
            return None
        video = session.get(_BASE_URL+video['pathFirstItem']).json()
        return None if not video.get('video') else video['video'].get('contentUrl')


def _relinker(url):
    # output=20 url in body
    # output=23 HTTP 302 redirect
    # output=25 url and other parameters in body, space separated
    # output=44 XML (not well formatted) in body
    # output=47 json in body
    # pl=native,flash,silverlight
    # A stream will be returned depending on the UA (and pl parameter?)
    scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
    query = urlparse.parse_qs(query)
    query['output'] = '20'
    query = urllib.urlencode(query, True)
    url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
            
    with client.Session() as session:
        session.headers.update({'User-Agent': _USER_AGENT})
        url = session.get(url).content.strip()
    
    # Workaround to normalize URL if the relinker doesn't
    url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
    
    return url
