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

from g2.libraries import client2

from .lib import jsunpack


_BASE_URL = 'http://www.cb01.co'
_SEARCH_QUERY = '/?s=%s'


def get_movie(dummy_module, title, year=None, **dummy_kwargs):
    title = title.translate(None, ':') # cb01 doesn't like the semicolons in the titles
    query = _SEARCH_QUERY % urllib.quote_plus('%s (%s)' % (title, year) if year else title)
    query = urlparse.urljoin(_BASE_URL, query)

    result = _cloudflare(query)

    result = result.decode('iso-8859-1').encode('utf-8')
    result = client2.parseDOM(result, 'div', attrs={'class': 'span12 filmbox'})
    result = [(client2.parseDOM(i, 'a', ret='href')[0], client2.parseDOM(i, 'h1')[0]) for i in result]
    result = [(u, unidecode(client2.replaceHTMLCodes(t))) for u, t in result]

    return [i for i in result
            if not re.search(r'\(\d{4}\)', i[1])
            or any(x in i[1] for x in ['(%s)'%str(y) for y in range(int(year)-1, int(year)+2)])]


def get_sources(dummy_module, ref):
    url, title = ref

    result = client2.request(url).content
    result = client2.parseDOM(result, 'table', attrs={})
    result = [t for t in result if 'Streaming:' in t][0]
    result = client2.parseDOM(result, 'td', attrs={})
    result = reduce(lambda x, y: x+y, [client2.parseDOM(t, 'td', attrs={}) for t in result], [])

    sources = []
    quality = 'SD'
    sources_area = False
    info = []
    for tdi in result:
        if 'Streaming' in tdi:
            sources_area = True
            if 'HD' in tdi:
                quality = 'HD'

        elif 'Download' in tdi:
            sources_area = False

        else:
            try:
                divs = client2.parseDOM(tdi, 'div', attrs={'align': 'right'})
                if divs:
                    nfo = client2.parseDOM(divs[0], 'strong')[0]
                    nfo = re.sub(r'<a.*?</a>', '', nfo)
                    info.append(unidecode(client2.replaceHTMLCodes(nfo)).strip())

                elif sources_area:
                    url = client2.parseDOM(tdi, 'a', ret='href')[0]
                    host = client2.parseDOM(tdi, 'a')[0]
                    sources.append({
                        'source': unidecode(client2.replaceHTMLCodes(host)),
                        'quality': quality,
                        'url': url,
                    })
            except Exception:
                pass

    for src in sources:
        src['info'] = ('' if not info else '[%s] '%(' '.join(info))) + title

    return sources


def resolve(dummy_module, url):
    result = client2.request(url).content if not 'go.php' in url else _cloudflare(url)

    scripts = client2.parseDOM(result, 'script')
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
        rurl = client2.parseDOM(result, 'a', attrs={'class': 'btn-wrapper'}, ret='href')[0]

    return rurl


def _cloudflare(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0',
    }

    with client2.Session(headers=headers) as session:
        res = session.request(url)

        if 'refresh' in res.headers:
            # refresh=8;URL=/cdn-cgi/l/chk_jschl?pass=1457690427.305-qGo9Ho8gdZ
            refresh_timeout = int(res.headers['refresh'][:1])
            refresh_url = res.headers['refresh'][6:]
            time.sleep(refresh_timeout)
            session.request(urlparse.urljoin(_BASE_URL, refresh_url))

        return session.request(url).content
