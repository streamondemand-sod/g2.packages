# -*- coding: utf-8 -*-

"""
    Genesi2 Add-on
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
import json
import urllib
import urlparse

from resources.lib import platform
from resources.lib import language

from resources.lib.libraries import client
from resources.lib.libraries import workers
from resources.lib.libraries import log

from resources.lib.dbs import tmdb


__all__ = ['url', 'movies']


netloc = ['predb.me']
priority = 9

_info_lang = platform.setting('infoLang') or 'en'

_urls = {
    'movies_recently_added{}': 'http://predb.me/?search=-MD&cats=movies&language=%s&page=1' % language.name(_info_lang)
}


def url(kind=None, **kwargs):
    if not kind: return _urls.keys()
    if kind not in _urls: return None

    for k, v in kwargs.iteritems():
        kwargs[k] = urllib.quote_plus(str(v))

    return _urls[kind].format(**kwargs)


def movies(url):
    try:
        result = client.request(url)
        results = client.parseDOM(result, 'div', attrs = {'class': 'post'})
        results = [(client.parseDOM(i, 'a', attrs = {'class': 'p-title.*?'}), re.compile('(\d{4}-\d{2}-\d{2})').findall(i)) for i in results]
        results = [(i[0][0], i[1][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0]
        results = [(re.sub('(\.|\(|\[|\s)(\d{4}|S\d*E\d*|3D)(\.|\)|\]|\s)(.+)', '', i[0]), re.compile('[\.|\(|\[|\s](\d{4})[\.|\)|\]|\s]').findall(i[0]), re.sub('[^0-9]', '', i[1])) for i in results]
        results = [(i[0], i[1][-1], i[2]) for i in results if len(i[1]) > 0]
        results = [(re.sub('(\.|\(|\[|LIMITED|UNCUT)', ' ', i[0]).strip(), i[1]) for i in results]
        results = [x for y, x in enumerate(results) if x not in results[0:y]]
        log.debug('predb.movies(%s): %s'%(url, results))
    except Exception as e:
        log.notice('predb.movies(%s): %s'%(url, e))
        return None

    items = []
    def predb_item(i, item):
        try:
            title, year = item
            item = tmdb.movies(tmdb.url('movies{title}{year}', title=title, year=year))
            if not item:
                log.debug('predb.movies(%s, %s): not found'%(title, year))
            else:
                item[0]['position'] = i
                items.append(item[0])
        except Exception as e:
            log.notice('predb.movies(%d): %s'%(item, e))

    try:
        page = int(re.search(r'&page=(\d+)', url).group(1))
        next_page = page + 1
        next_url = url.replace('&page=%d'%page, '&page=%d'%next_page)
    except:
        next_url = ''
        next_page = 0

    threads = []
    for i, item in enumerate(results):
        threads.append(workers.Thread(predb_item, i, item))
    [i.start() for i in threads]
    [i.join() for i in threads]

    for i in items:
        i['next_url'] = next_url
        i['next_page'] = next_page

    items = sorted(items, key=lambda x: x['position'])

    return items
