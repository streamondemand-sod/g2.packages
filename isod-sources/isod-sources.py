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
import re
import sys
import urllib
import urlparse

import xbmcaddon
import importer

from resources.lib.libraries import cleantitle
from resources.lib.libraries import client
from resources.lib.libraries import log


__all__ = ['info', 'get_movie', 'get_sources']


_sod_addon_channels_package = 'channels'
_sod_addon_channels_path = os.path.join(xbmcaddon.Addon('plugin.video.streamondemand').getAddonInfo('path'), _sod_addon_channels_package)

_excluded_channels = [
    'biblioteca',       # global search channel
    'buscador',         # global search channel
    'corsaronero',      # torrent only
]


def _info():
    from core import logger
    logger.log_enable(False)

    info = []
    for package, module, is_pkg in importer.walk_packages([_sod_addon_channels_path]):
        if is_pkg or module in _excluded_channels: continue
        try:
            m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [module], -1), module)
        except Exception as e:
            log.notice('isod-sources: from %s import %s: %s'%(_sod_addon_channels_package, module, e))
            continue
        if hasattr(m, 'search'):
            log.debug('isod-sources: submodule %s added'%module)
            info.append({'name': module})

    return info


info = _info()


def get_movie(module, title, year, language='it', **kwargs):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [module[2]], -1), module[2])
    except Exception as e:
        log.notice('isod-sources.%s.get_movie(...): %s'%(module[2], e))
        return None

    try:
        title_search = normalize_unicode(title, encoding='ascii')
        title_search = urllib.quote_plus(title_search)
        items = m.search(Item(), title_search)
        if not items: return None
    except Exception as e:
        log.notice('isod-sources.%s.get_movie(%s, %s, %s): %s'%(module[2], title, year, language, e))
        return None

    # TODO: [(year)] filtering if returned in the title
    # TODO: [(sub-ita)] filtering if returned in the title
    from lib.fuzzywuzzy import fuzz

    def cleanup(title):
        # Clean up a bit the returned title to improve the fuzzy matching
        title = re.sub(r'\(.*\)', '', title)  # Anything within ()
        title = re.sub(r'\[.*\]', '', title)  # Anything within []
        return title

    item = sorted(items, key=lambda i: fuzz.token_sort_ratio(cleanup(i.fulltitle), title), reverse=True)[0]

    quality = 'HD' if re.search(r'[^\w]HD[^\w]', item.fulltitle) else ''

    log.notice('isod-sources.%s.get_movie(...): %d matches, best fuzzy score=%d, quality=%s, title=%s'%
               (module[2], len(items), fuzz.token_sort_ratio(cleanup(item.fulltitle), title), quality, item.fulltitle))

    # TODO[user]: use fuzziness parameter (user setting) instead of 84, also enable the user to change it on the fly via ctx menu
    return None if fuzz.token_sort_ratio(cleanup(item.fulltitle), title) < 84 else '%s|%s|%s'%(item.action, item.url, quality)


def get_sources(module, url):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [module[2]], -1), module[2])
    except Exception as e:
        log.notice('isod-sources.%s: %s'%(module[2], e))
        return []

    action, url, url_quality = url.split('|')
    item = Item(action=action, url=url)

    try:
        if hasattr(m, item.action):
            # Channel specific function to retrieve the sources
            sitems = getattr(m, item.action)(item)
        else:
            # Generic function to retrieve the sources
            item.action = 'servertools.find_video_items'
            sitems = servertools.find_video_items(item)
    except:
        sitems = []

    if sitems == []:
        log.debug('isod-sources.get_sources: %s.%s: no sources for url=%s'%(module[2], item.action, item.url))

    sources = {}
    for sitem in sitems:
        if sitem.action != 'play':
            log.debug('isod-sources.get_sources: %s.%s: play action not specified for url=%s'%(module[2], item.action, sitem.url))
            continue

        t = sitem.title
        # Extract the stream quality if provided in the title
        quality = 'HD' if re.search(r'[^\w]HD[^\w]', t) else url_quality if url_quality else 'SD'
        # Remove known tags and year
        t = re.sub(r'\[HD\]', '', t)
        t = re.sub(r'\(\d{4}\)', '', t)
        # Remove the [COLOR ...]<info>[/COLOR] tags and collect the <info>
        info_tags = [module[2]]
        def collect_color_tags(match):
            info_tags.append(match.group(1))
            return ''
        t = re.sub(r'\[COLOR\s+[^\]]+\]([^\[]*)\[/COLOR\]', collect_color_tags, t)
        t = re.sub(r'\[/?COLOR[^\]]*\]', '', t)
        # Extract the host if possible
        try:
            host = re.search(r'\s+-\s+\[([^\]]+)\]', t).group(1)
        except:
            try:
                host = re.search(r'\[([^\]]+)\]', t).group(1)
            except:
                host = ''
        host = host.split(' ')[-1].translate(None, '@')

        if not hasattr(m, sitem.action):
            # No channel specific resolver
            url = sitem.url
            action = ''
        else:
            # Channel specific resolver to run first
            try:
                pitems = getattr(m, sitem.action)(sitem)
            except:
                pitems = []
            if len(pitems) == 0:
                log.debug('isod-sources.get_sources: %s.%s: no sources for url=%s'%(module[2], sitem.action, sitem.url))
                continue
            url = pitems[0].url
            action = pitems[0].action

        log.debug('isod-sources.get_sources: %s.%s: host=%s, quality=%s, url=%s, action=%s, title=%s'%(
            module[2], sitem.action, host, quality, url, action, sitem.title))
        sources[url] = {'source': host, 'quality': quality, 'info': ' '.join(info_tags), 'url': url}

    return sources.values()


def normalize_unicode(string, encoding='utf-8'):
    from unicodedata import normalize
    if string is None: string = ''
    return normalize('NFKD', string if isinstance(string, unicode) else unicode(string, encoding, 'ignore')).encode(encoding, 'ignore')
