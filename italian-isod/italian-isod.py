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

import xbmc
import xbmcaddon
try:
    import importer
except:
    import pkgutil as importer

from resources.lib.libraries import cleantitle
from resources.lib.libraries import client
from resources.lib.libraries import log


__all__ = ['sub_modules', 'get_movie', 'get_sources']


sod_addon_id = 'plugin.video.streamondemand'
sod_addon_channels_package = 'channels'
sod_addon_channels_path = os.path.join(xbmcaddon.Addon(sod_addon_id).getAddonInfo('path'), sod_addon_channels_package)

_excluded_channels = [
    'biblioteca',       # global search channel
    'buscador',         # global search channel
    'corsaronero',      # torrent only
]

if xbmc.getCondVisibility('System.HasAddon(%s)'%sod_addon_id):
    sub_modules = []
    for package, module, is_pkg in importer.walk_packages([sod_addon_channels_path]):
        if is_pkg or module in _excluded_channels: continue
        try:
            m = getattr(__import__(sod_addon_channels_package, globals(), locals(), [module], -1), module)
        except Exception as e:
            log.notice('italian-isod: from %s import %s: %s'%(sod_addon_channels_package, module, e))
            continue
        if hasattr(m, 'search'):
            sub_modules.append(module)

    # TODO: enable/disable logging could be a configurable option
    from core import logger
    logger.log_enable(False)


def get_movie(module, dbids, title, year, language='it'):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(sod_addon_channels_package, globals(), locals(), [module[2]], -1), module[2])
    except Exception as e:
        log.notice('italian-isod.get_movie: %s: %s'%(module[2], e))
        return None
    try:
        items = m.search(Item(), title)
    except Exception as e:
        log.notice('italian-isod.get_movie: %s.search(%s, %s, %s): %s'%(module, title, year, language, e))
        return None

    cleartitle = cleantitle.movie(title)
    # TODO: [(year)] filtering if returned in the title
    # TODO: [(sub-ita)] filtering if returned in the title
    items = [item for item in items if cleartitle == cleantitle.movie(item.fulltitle)]

    if len(items) > 1:
        log.notice('italian-isod.get_movie: %s.search(%s, %s, %s): %d matches'%(module, title, year, language, len(items)))

    return None if items == [] else '%s@%s'%(items[0].action, items[0].url)


def get_sources(module, url):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(sod_addon_channels_package, globals(), locals(), [module[2]], -1), module[2])
    except Exception as e:
        log.notice('italian-isod.%s: %s'%(module[2], e))
        return []

    action, url = url.split('@', 1)
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
        log.debug('italian-isod.get_sources: %s.%s: no sources for url=%s'%(module[2], item.action, item.url))

    sources = {}
    for sitem in sitems:
        if sitem.action != 'play':
            log.debug('italian-isod.get_sources: %s.%s: play action not specified for url=%s'%(module[2], item.action, sitem.url))
            continue

        t = sitem.title
        # Extract the stream quality if provided in the title
        quality = 'HD' if re.search(r'[^\w]HD[^\w]', t) else 'SD'
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
                log.debug('italian-isod.get_sources: %s.%s: no sources for url=%s'%(module[2], sitem.action, sitem.url))
                continue
            url = pitems[0].url
            action = pitems[0].action

        log.debug('italian-isod.get_sources: %s.%s: host=%s, quality=%s, url=%s, action=%s, title=%s'%(
            module[2], sitem.action, host, quality, url, action, sitem.title))
        sources[url] = {'source': host, 'quality': quality, 'info': ' '.join(info_tags), 'url': url}

    return sources.values()
