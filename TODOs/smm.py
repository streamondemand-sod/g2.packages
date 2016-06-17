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

from libraries import log

from metahandler import metahandlers


info = {
    'domains': [],
    'methods': ['url', 'watched'],
}

_urls = {
    'watched.movie{imdb_id}': 'movie.imdb.{imdb_id}',
}


def url(kind=None, **kwargs):
    if not kind: return _urls.keys()
    if kind not in _urls: return None

    for k, v in kwargs.iteritems():
        kwargs[k] = urllib.quote_plus(str(v))

    return _urls[kind].format(**kwargs)


def watched(kind, seen=None, **kwargs):
    url_ = url(kind, **kwargs)
    log.notice('metahandler.watched: url(%s, %s)=%s'%(kind, kwargs, url_))
    if not url_:
        return None

    content, id_type, id_value = url_.split('.')
    if id_type != 'imdb':
        return None

    # TODO[code]: manage TMDB key centrally (user setting?)
    metaget = metahandlers.MetaData(preparezip=False, tmdb_api_key='f7f51775877e0bb6703520952b3c7840')
    if seen is None:
        meta = metaget._cache_lookup_by_id(content, imdb_id=id_value)
        log.debug('metahandler.watched: _cache_lookup_by_id(%s, imdb_id=%s)=%s'%(content, id_value, meta))
        return None if not meta else meta.get('overlay') == 7
    else:
        metaget.get_meta(content, '', imdb_id=id_value)
        metaget.change_watched(content, '', imdb_id=id_value, watched=7 if seen else 6)
        log.debug('metahandler.watched: change_watched(%s, "", %s, watched=%s) done'%(content, id_value, 7 if seen else 6))
        return None # Give a change to the other backends to store the flag too!


"""
    When adding a DBS method please include its name in info['methods']!!!
"""
