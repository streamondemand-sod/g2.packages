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

import os
import pkgutil
import re
import sys
import urllib
import urlparse

import xbmcaddon

from resources.lib.libraries import cleantitle
from resources.lib.libraries import client
from resources.lib.libraries import log

class Item:
    def __init__(self, category=''):
        self.category = category
        self.channel = ''
        self.extra = category
        self.url = ''

sod_addon_path = xbmcaddon.Addon('plugin.video.streamondemand').getAddonInfo('path')
sys.path.append(sod_addon_path)

from servers import servertools

exclude = [
    'biblioteca',       # global search channel
    'buscador',         # global search channel
    'corsaronero',      # torrent only
]


def get_movie(dbids, title, year, language='it'):
    return urllib.urlencode({
        'title': title,
        'year': year,
        'language': language,
        })


def get_sources(url):
    query = urlparse.parse_qs(url)
    title = query['title'][0]
    year = query['year'][0]
    language = query['language'][0]
    cleartitle = cleantitle.movie(title)

    sources = {}
    for package, module, is_pkg in pkgutil.walk_packages([os.path.join(sod_addon_path, 'channels')]):
        if is_pkg or module in exclude: continue

        try:
            m = getattr(__import__('channels', globals(), locals(), [module], -1), module)
        except Exception as e:
            import traceback
            log.notice(traceback.format_exc())
            continue
        if not hasattr(m, 'search'): continue

        try:
            items = m.search(Item(), title)
        except:
            import traceback
            log.notice(traceback.format_exc())
            continue

        items = [item for item in items if cleartitle == cleantitle.movie(item.fulltitle)]
        if items == []:
            log.debug('italian-isod.get_sources: %s.search: no title matches'%module)

        for i, item in enumerate(items):
            if hasattr(m, item.action):
                # Channel specific function to retrieve the sources
                sitems = getattr(m, item.action)(item)
            else:
                # Generic function to retrieve the sources
                sitems = servertools.find_video_items(item)

            if sitems == []:
                log.debug('italian-isod.get_sources: %s.search[%d]: no sources for url=%s'%(module, i+1, item.url))

            for j, sitem in enumerate(sitems):
                if sitem.action != 'play':
                    log.debug('italian-isod.get_sources: %s.search[%d/%d]: no play action for url=%s'%(module, i+1, j+1, sitem.url))
                    continue

                t = sitem.title
                # Extract the stream quality if provided in the title
                quality = 'HD' if re.search(r'\s+\[HD\]\s+', t) else 'SD'
                # Remove known tags and year
                t = re.sub(r'\[HD\]', '', t)
                t = re.sub(r'\(\d{4}\)', '', t)
                t = re.sub(r'\[/?COLOR[^\]]*\]', '', t)
                # Extract the host if possible
                try:
                    host = re.search(r'\s+-\s+\[([^\]]+)\]', t).group(1)
                except:
                    try:
                        host = re.search(r'\[([^\]]+)\]', t).group(1)
                    except:
                        host = ''

                if not hasattr(m, sitem.action):
                    # No channel specific resolver
                    url = sitem.url
                else:
                    # Channel specific resolver to run first
                    pitems = getattr(m, sitem.action)(sitem)
                    if len(pitems) == 0:
                        log.debug('italian-isod.get_sources: %s.search[%d/%d]: no sources for url=%s'%(
                            module, i+1, j+1, sitem.url))
                        continue
                    url = pitems[0].url
                log.debug('italian-isod.get_sources: %s.search[%d/%d]: host=%s, quality=%s, url=%s, title=%s'%(
                    module, i+1, j+1, host, quality, url, sitem.title))
                sources[url] = {'source': host, 'quality': quality, 'info': module, 'url': url}

    return sources.values()
