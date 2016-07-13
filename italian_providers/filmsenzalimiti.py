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
import urllib
import urlparse

from unidecode import unidecode

from g2.libraries import log
from g2.libraries import client


_BASE_LINK = 'http://www.filmsenzalimiti.co'
_SEARCH_QUERY = '/?s=%s'


def get_movie(dummy_module, title, **dummy_kwargs):
    return _do_search(title)


def get_episode(dummy_module, tvshowtitle, season, episode, **dummy_kwargs):
    items = _do_search(tvshowtitle)
    for i in range(len(items)):
        items[i] += (season, episode,)

    return items


def _do_search(title):
    query = _SEARCH_QUERY % urllib.quote_plus(title)
    query = urlparse.urljoin(_BASE_LINK, query)

    result = client.request(query).content
    result = result.decode('utf-8')
    result = client.parseDOM(result, 'div', attrs={'class': 'post-item-side'})

    return [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'img', ret='title')[0]) for i in result]


def get_sources(dummy_module, vref):
    if len(vref) == 2:
        return _get_movie_sources(*vref)
    elif len(vref) == 4:
        return _get_episode_sources(*vref)
    else:
        return []


def _get_movie_sources(url, title):
    result = client.request(url).content
    result = result.decode('utf-8')

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


def _get_episode_sources(url, tvshowtitle, season, episode):
    result = client.request(url).content
    result = result.decode('utf-8')

    result = client.parseDOM(result, 'div', attrs={'class': 'entry'})
    seasons = client.parseDOM(result[0], 'p')
    episode_patobj = re.compile(r'(?:^|[^\d])(\d{1,2})x(\d{1,2})\s*')
    nfo = []
    quality = 'SD'
    sources = []
    for season_dom in seasons:
        season_dom = client.replaceHTMLCodes(season_dom)
        if 'stagione' in season_dom.lower():
            season_dom = season_dom.replace('<strong>', '')
            season_dom = season_dom.replace('</strong>', '')
            season_dom = season_dom.replace('<br />', '')
            nfo = [season_dom.strip()]
            continue

        while True:
            match = episode_patobj.search(unidecode(season_dom))
            if not match:
                break

            e_season = str(int(match.group(1)))
            e_episode = str(int(match.group(2)))

            br_position = season_dom.find('<br')
            episode_dom = season_dom[:br_position]
            season_dom = season_dom[br_position+4 if br_position > 0 else -1:]

            urls = client.parseDOM(episode_dom, 'a', ret='href')
            hosts = client.parseDOM(episode_dom, 'a')

            for url, host in zip(urls, hosts):
                sources.append({
                    'url': url,
                    'source': unidecode(host),
                    'quality': quality,
                    'info': ' / '.join(nfo),
                    'season': e_season,
                    'episode': e_episode,
                })

    return sources
