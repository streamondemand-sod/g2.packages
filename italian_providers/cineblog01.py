# -*- coding: utf-8 -*-

"""
    G2 Add-on Package
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

from unidecode import unidecode

from g2.libraries import client

from .lib import jsunpack


_BASE_LINK = 'http://www.cb01.co'
_SEARCH_LINK = '/?s=%s'


def get_movie(dummy_module, title, year=None, **dummy_kwargs):
    title = title.translate(None, ':') # cb01 doesn't like the semicolons in the titles
    query = _SEARCH_LINK % urllib.quote_plus('%s (%s)' % (title, year) if year else title)
    query = urlparse.urljoin(_BASE_LINK, query)

    result = _cloudflare(query)

    result = result.decode('iso-8859-1').encode('utf-8')
    result = client.parseDOM(result, 'div', attrs={'class': 'span12 filmbox'})
    result = [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'h1')[0]) for i in result]
    result = [(u, unidecode(client.replaceHTMLCodes(t))) for u, t in result]

    # (fixme): [(sub-ita)] filtering if returned in the title and language is provided

    return [i for i in result
            if not re.search(r'\(\d{4}\)', i[1])
            or any(x in i[1] for x in ['(%s)'%str(y) for y in range(int(year)-1, int(year)+2)])]


def get_sources(dummy_module, ref):
    url, title = ref

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
                try:
                    nfo = re.search(r'</a>(.+)</strong>', i).group(1)
                    info.append(unidecode(client.replaceHTMLCodes(nfo)).strip())
                except Exception:
                    pass
            elif 'HD' in i:
                # Check for the HD section
                quality = 'HD'
            else:
                # Retrieve some info about the source (2nd format)
                try:
                    nfo = re.search(r'<div align="right"><strong>.*?([A-Za-z0-9\.]+)</strong>', i).group(1)
                    info.append(unidecode(client.replaceHTMLCodes(info)).strip())
                except Exception:
                    pass
        elif not ignoresources:
            for url, host in zip(client.parseDOM(i, 'a', ret='href'), client.parseDOM(i, 'a')):
                sources.append({
                    'source': unidecode(client.replaceHTMLCodes(host)),
                    'quality': quality,
                    'url': url,
                })

    for src in sources:
        src['info'] = ('' if not info else '[%s] '%(' '.join(info))) + title

    return sources


def resolve(dummy_module, url):
    result = client.request(url) if not 'go.php' in url else _cloudflare(url)

    scripts = client.parseDOM(result, 'script')
    rurl = None
    for i in scripts:
        match = re.search(r'(eval\(function\(p,a,c,k,e,d.*)', i)
        if match:
            i = jsunpack.unpack(match.group(1))

        match = re.search(r'var link\s*=\s*"([^"]+)";', i)
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


def _cloudflare(url):
    rheaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0',
    }

    # Do expect an HTTP error on the first request
    headers = client.request(url, headers=rheaders, referer=_BASE_LINK, output='headers', error=True)

    if not 'refresh' in headers:
        cookie = None
    else:
        # refresh=8;URL=/cdn-cgi/l/chk_jschl?pass=1457690427.305-qGo9Ho8gdZ
        refresh_timeout = int(headers['refresh'][:1])
        refresh_url = headers['refresh'][6:]
        time.sleep(refresh_timeout)

        url_cookie = '%s://%s' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)
        cookie = client.request(urlparse.urljoin(url_cookie, refresh_url), headers=rheaders, output='cookie')

    return client.request(url, headers=rheaders, cookie=cookie)
