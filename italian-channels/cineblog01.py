# -*- coding: utf-8 -*-

"""
    Genesi2 Add-on Package
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

import re
import time
import urllib
import urlparse
import unidecode

from resources.lib.libraries import cleantitle
from resources.lib.libraries import client

from lib import jsunpack


# TODO: Remove the class object and implement as an hierarchy like the resolvers
class source:
    def __init__(self):
        self.base_link = 'http://www.cb01.co'
        self.search_link = '/?s=%s'
        self.provider = 'cineblog01'    # TODO: this has to match the filename, so it should be automatically set
        # TODO: add the self.language attribute to identify in which language the search are answered

    def get_movie(self, dbids, title, year, language='it'):
	"""
        Input:
            dbids       A dictionary with the identifier of the title in varius DB (imdb, tmdb)
            title       The movie title
            year        The movie release year
            language    The ISO [639-1] two letter language identifier used for the title search

        Output: The url to movie page in the source web site containing the sources (passed as 1st argument to get_sources)

        NOTE: the output url is cached for later reuse.
	"""
        query = self.search_link % urllib.quote_plus(title)
        query = urlparse.urljoin(self.base_link, query)

        # Manage Clouflare frontend
        result = self.cloudflare(query)

        # Parse the result page
        result = client.parseDOM(result, 'div', attrs={'class': 'span12 filmbox'})
        result = [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'h1')[0]) for i in result]
        result = [(u, unidecode.unidecode(client.replaceHTMLCodes(t))) for u, t in result]

        # Filter by title / language
        title = cleantitle.movie(title)
        if language is None or language == 'it':
            # If the search language is italian, ignore the sub-ita titles
            result1 = [i for i in result if not re.search(r'SUB-ITA', i[1], flags=re.IGNORECASE)]
            result2 = [i for i in result1 if title == cleantitle.movie(i[1])]
        else:
            # If the search language is NOT italian, do include only the sub-ita titles
            result1 = [i for i in result if re.search(r'SUB-ITA', i[1], flags=re.IGNORECASE)]
            result2 = [i for i in result1 if title == cleantitle.movie(i[1])]
            # If no title matches, then try to compare the titles by first removing the italian title version:
            # For example, the title:
            #   '90 Minutes in Heaven - 90 minuti in Paradiso [Sub-ITA] (2015)'
            # become:
            #   '90 Minutes in Heaven [Sub-ITA] (2015)'
            if len(result2) == 0:
                result2 = [i for i in result1 if title == cleantitle.movie(re.sub(r'\s+-\s+[^\[\(]+', ' ', i[1]))]

        # If the default title filter is too strict, then relax it ignoring the presence or not of the sub-ita tag
        result = result2 if len(result2) else [i for i in result if title == cleantitle.movie(i[1])]

        # Filter by year only if the extracted title contains the year itself in the format '(YEAR)'
        url = [i[0] for i in result if not re.search(r'\(\d{4}\)', i[1]) or any(x in i[1] for x in ['(%s)'%str(y) for y in range(int(year)-1,int(year)+2)])][0]

        url = urlparse.urlparse(url).path

        return url

    def get_sources(self, url):
	"""
        Input:
            url         The url previously returned by the get_movie/get_episode

        Output: A list of dictionary with the following attributes:
            source:     The resolver (host) of the content
            quality:    An indication of the quality level using the following keywords: '1080p' | 'HD' | 'SD' | 'SCR' | 'CAM'
            provider:   This module identifier, typically set in self.provider
            info:       Additional info the provider has about the media (e.g. DVDRip or MD)
            url:        The content url to be resolved

        NOTE: the output list is cached for later reuse.
	"""
        url = urlparse.urljoin(self.base_link, url)

        result = client.request(url)

        result = result.decode('iso-8859-1').encode('utf-8')
        result = client.parseDOM(result, 'div', attrs={'class': 'post_content'})
        result = client.parseDOM(result, 'td', attrs={'valign': 'top'})
        result = client.parseDOM(result, 'table', noattrs=False)

        sources = []
        quality = 'SD'
        ignoresources = False
        info = []
        for i in result:
            if client.parseDOM(i, 'strong'):
                if 'Download' in i or '3D' in i:
                    # Ignore Download / 3D section for now
                    ignoresources = True
                elif 'Screen/Report' in i:
                    # Retrieve some info about the source (1st format)
                    try: info.append(cleantitle.normalize2(client.replaceHTMLCodes(re.search(r'</a>(.+)</strong>', i).group(1))).strip())
                    except: pass
                elif 'HD' in i:
                    # Check for the HD section
                    quality = 'HD'
                else:
                    # Retrieve some info about the source (2nd format)
                    try: info.append(cleantitle.normalize2(client.replaceHTMLCodes(re.search(r'<div align="right"><strong>.*?([A-Za-z0-9\.]+)</strong>', i).group(1))).strip())
                    except: pass
            elif not ignoresources:
                for url, host in map(None, client.parseDOM(i, 'a', ret='href'), client.parseDOM(i, 'a')):
                    sources.append({'source': cleantitle.normalize2(client.replaceHTMLCodes(host)), 'quality': quality, 'provider': self.provider, 'url': url})

        if len(info):
            for s in sources: s['info'] = ', '.join(info)

        return sources

    def resolve(self, url):
	"""
        Input:
            url         The url returned by the get_sources

        Output: the url to be resolved via the resolvers

        NOTE: this method is optional if the sources site provides the url ready for the resolvers
	"""
        result = client.request(url) if not 'go.php' in url else self.cloudflare(url)

        scripts = client.parseDOM(result, 'script')
        rurl = None
        for i in scripts:
            match = re.search('(eval\(function\(p,a,c,k,e,d.*)', i)
            if match:
                i = jsunpack.unpack(match.group(1))

            match = re.search('var link\s*=\s*"([^"]+)";', i)
            if match:
                rurl = match.group(1)
                break

            match = re.search('window.location.href = "([^"]+)";', i)
            if match:
                rurl = match.group(1)
                break

        if not rurl:
            rurl = client.parseDOM(result, 'a', attrs={'class': 'btn-wrapper'}, ret='href')[0]

        return rurl

    def cloudflare(self, url):
        rheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0' }

        # Do expect an HTTP error on the first request
        headers = client.request(url, headers=rheaders, referer=self.base_link, output='headers', error=True)

        if not 'refresh' in headers:
            cookie = None
        else:
            # refresh=8;URL=/cdn-cgi/l/chk_jschl?pass=1457690427.305-qGo9Ho8gdZ
            refresh_timeout = int(headers['refresh'][:1])
            refresh_url = headers['refresh'][6:]
            time.sleep(refresh_timeout)

            u = '%s://%s' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)
            cookie = client.request('%s%s'%(u, refresh_url), headers=rheaders, referer=self.base_link, output='cookie')

        return client.request(url, headers=rheaders, referer=self.base_link, cookie=cookie)
