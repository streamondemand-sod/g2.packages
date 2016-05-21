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

import importer

from libraries import log
from libraries import cleantitle
from libraries import client


_sod_addon_channels_package = 'channels'

_excluded_channels = [
    'biblioteca',       # global search channel
    'buscador',         # global search channel
    'corsaronero',      # torrent only
    'tengourl',         # not a title search channel
]

_channels_options = {
    'cineblog01': {
        'source_quality_override': True,
        'ignore_tags': ['Streaming HD:', 'Streaming:'],
        'use_year': True,
    },
}


def _channel_option(channel, option, default=None):
    return _channels_options.get(channel, {}).get(option, default)


def info(paths):
    from core import logger
    logger.log_enable(False)

    info = []
    for package, channel, is_pkg in importer.walk_packages([os.path.join(paths[0], _sod_addon_channels_package)]):
        if is_pkg or channel in _excluded_channels: continue
        try:
            m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [channel], -1), channel)
        except Exception as e:
            log.notice('isod-sources: from %s import %s: %s'%(_sod_addon_channels_package, channel, e))
            continue
        if hasattr(m, 'search'):
            log.debug('isod-sources: channel %s added'%channel)
            info.append({'name': channel})

    return info


def get_movie(provider, title, year=None, language='it', **kwargs):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [provider[2]], -1), provider[2])
    except Exception as e:
        log.notice('isod-sources.get_movie(%s, ...): %s'%(provider[2], e))
        return None

    try:
        search_terms = normalize_unicode(title, encoding='ascii')
        if year and _channel_option(provider[2], 'use_year'):
            search_terms += ' (%s)'%year
        items = m.search(Item(), urllib.quote_plus(search_terms))
        if not items: return None
    except Exception as e:
        log.notice('isod-sources.get_movie(%s, %s, ...): %s'%(provider[2], title, e))
        return None

    # TODO: [(year)] filtering if returned in the title and year is provided
    # TODO: [(sub-ita)] filtering if returned in the title and language is provided

    def cleantitle(title):
        title = re.sub(r'\(.*\)', '', title)  # Anything within ()
        title = re.sub(r'\[.*\]', '', title)  # Anything within []
        return title

    # NOTE: list of tuples: (url, matched_title[, additional_infos...])
    return [(i.url, cleantitle(i.fulltitle), i.action, 'HD' if re.search(r'[^\w]HD[^\w]', i.fulltitle) else 'SD') for i in items]


def get_sources(provider, vref):
    from servers import servertools
    from core.item import Item

    try:
        m = getattr(__import__(_sod_addon_channels_package, globals(), locals(), [provider[2]], -1), provider[2])

        url, title, action, ref_quality = vref
        item = Item(action=action, url=url)

        if hasattr(m, item.action):
            # Channel specific function to retrieve the sources
            sitems = getattr(m, item.action)(item)
        else:
            # Generic function to retrieve the sources
            item.action = 'servertools.find_video_items'
            sitems = servertools.find_video_items(item)
    except Exception as e:
        log.notice('isod-sources.get_sources(%s, ...): %s'%(provider[2], e))
        return []

    if not sitems:
        log.debug('isod-sources.get_sources(%s, ...): no sources found by %s(%s)'%(provider[2], item.action, item.url))

    sources = {}
    for sitem in sitems:
        if sitem.action != 'play':
            log.debug('isod-sources.get_sources(%s, ...): play action not specified for source %s'%(provider[2], sitem.__dict__))
            continue

        log.debug('isod-sources.get_sources(%s, ...): processing source %s'%(provider[2], sitem.__dict__))

        t = sitem.title        

        # Extract the stream quality if provided in the title, otherwise fallback to the quality
        # found in the sources page title but not if 'source_quality_override' is a channel option (e.g. cineblog01)
        quality = 'HD' if re.search(r'[^\w]HD[^\w]', t) else 'SD' if _channel_option(provider[2], 'source_quality_override') else ref_quality

        # Remove known tags and year
        t = re.sub(r'\[HD\]', '', t)
        t = re.sub(r'\(\d{4}\)', '', t)
        # Remove the [COLOR ...]<info>[/COLOR] tags and collect the <info>
        info_tags = []
        def collect_color_tags(match):
            tag = match.group(1)
            if tag not in _channel_option(provider[2], 'ignore_tags', []):
                info_tags.append(tag)
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
            if not len(pitems):
                log.debug('isod-sources.get_sources(%s, ...): url cannot be resolved for source %s'%(provider[2], sitem.__dict__))
                continue
            url = pitems[0].url
            action = pitems[0].action

        sources[url] = {'source': host, 'quality': quality, 'info': ('[%s] '%' '.join(info_tags) if info_tags else '')+title, 'url': url}

        log.debug('isod-sources.get_sources(%s, ...): %s'%(provider[2], sources[url]))

    return sources.values()


def normalize_unicode(string, encoding='utf-8'):
    from unicodedata import normalize
    if string is None: string = ''
    return normalize('NFKD', string if isinstance(string, unicode) else unicode(string, encoding, 'ignore')).encode(encoding, 'ignore')
