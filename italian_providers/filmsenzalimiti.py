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

import urllib
import urlparse

from unidecode import unidecode

from g2.libraries import client


_BASE_LINK = 'http://www.filmsenzalimiti.co'
_SEARCH_LINK = '/?s=%s'


def get_movie(dummy_module, title, **dummy_kwargs):
    query = _SEARCH_LINK % urllib.quote_plus(title)
    query = urlparse.urljoin(_BASE_LINK, query)

    result = client.request(query)

    result = client.parseDOM(result, 'div', attrs={'class': 'post-item-side'})[0]
    urls = client.parseDOM(result, 'a', ret='href')
    titles = client.parseDOM(result, 'img', attrs={'class': 'post-side-img'}, ret='title')
    titles = [unidecode(client.replaceHTMLCodes(t)) for t in titles]

    return zip(urls, titles)


def get_sources(dummy_module, ref):
    url, title = ref

    result = client.request(url)

    result = result.decode('iso-8859-1').encode('utf-8')
    result = client.parseDOM(result, 'ul', attrs={'class': 'host'})[1]

    # E.g. <span class="b"><img src="http://imagerip.net/images/2015/08/14/rapidvideo.png"
    #       alt="Rapidvideo" height="10"> Rapidvideo</span>
    names = [client.parseDOM(i, 'img', ret='alt')[0] for i in client.parseDOM(result, 'span', attrs={'class': 'b'})]

    # E.g. <a href="http://www.rapidvideo.org/eskf5x2cqghi/Deadpool.2016.iTALiAN.MD.TS.XviD-iNCOMiNG.avi.html"
    #       rel="nofollow" target="_blank" class="external">
    urls = client.parseDOM(result, 'a', attrs={'class': 'external'}, ret='href')

    # E.g. <span class="a"><i class="fa fa-circle-o fa-lg"></i> Streaming</span>
    actions = client.parseDOM(result, 'span', attrs={'class': 'a'})

    # E.g. <span class="d">360p</span>
    qualities = client.parseDOM(result, 'span', attrs={'class': 'd'})

    # E.g. <a href="http://www.filmsenzalimiti.co/genere/subita" rel="category tag">Film Sub Ita</a>
    info = client.parseDOM(result, 'a', attrs={'rel': r'category\s+tag'})

    sources = []
    for name, url, action, quality in zip(names, urls, actions, qualities):
        if action and 'Streaming' in action:
            quality = 'HD' if quality.strip() in ['720p', '1080p'] else 'SD'
            sources.append({
                'source': name.encode('utf-8'),
                'quality': quality,
                'url': url.encode('utf-8'),
                'info': ('' if not info else '[%s] '%(' '.join(info))) + title,
            })

    return sources