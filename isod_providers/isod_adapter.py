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

import os
import re
import urllib

import importer

from unidecode import unidecode

from g2.libraries import log
from g2.libraries import client


_SOD_ADDON_CHANNELS_PACKAGE = 'channels'

_EXCLUDED_CHANNELS = [
    'biblioteca',       # global search channel
    'buscador',         # global search channel
    'corsaronero',      # torrent only
    'tengourl',         # not a title search channel
]

_CHANNELS_OPTIONS = {
    'cineblog01': {
        'remove_chars': ':',
        'use_year': ' (%s)',
        'source_quality_override': True,
        'ignore_tags': ['Streaming HD:', 'Streaming:'],
    },
    # (fixme) other channels might need custome flags as well...
}


def _channel_option(channel, option, default=None):
    return _CHANNELS_OPTIONS.get(channel, {}).get(option, default)


def info(paths):
    from core import logger
    logger.log_enable(False)

    nfo = []
    for dummy_package, channel, is_pkg in importer.walk_packages([os.path.join(paths[0], _SOD_ADDON_CHANNELS_PACKAGE)]):
        if is_pkg or channel in _EXCLUDED_CHANNELS:
            continue
        try:
            mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [channel], -1), channel)
        except Exception as ex:
            log.error('{m}.{f}: from %s import %s: %s', _SOD_ADDON_CHANNELS_PACKAGE, channel, ex)
            continue
        if hasattr(mod, 'search'):
            log.notice('{m}.{f}: channel %s added', channel)
            nfo.append({'name': channel})

    return nfo


def get_movie(provider, title, year=None, **kwargs):
    from servers import servertools
    from core.item import Item

    try:
        mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [provider[2]], -1), provider[2])
    except Exception as ex:
        log.error('{m}.{f}.get_movie(%s, ...): %s', provider[2], ex)
        return None

    try:
        if _channel_option(provider[2], 'remove_chars'):
            title = title.translate(None, _channel_option(provider[2], 'remove_chars'))
        search_terms = unidecode(title)
        if year and _channel_option(provider[2], 'use_year'):
            search_terms += _channel_option(provider[2], 'use_year') % year
        items = mod.search(Item(), urllib.quote_plus(search_terms))
        if not items:
            return None
    except Exception as ex:
        log.notice('{m}.{f}.get_movie(%s, %s, ...): %s', provider[2], title, ex)
        return None

    # (fixme): [(year)] filtering if returned in the title and year is provided
    # (fixme): [(sub-ita)] filtering if returned in the title and language is provided

    return [(i.url, i.fulltitle, i.action, 'HD' if re.search(r'[^\w]HD[^\w]', i.fulltitle) else 'SD') for i in items]


def get_sources(provider, vref):
    from servers import servertools
    from core.item import Item

    try:
        mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [provider[2]], -1), provider[2])

        url, title, action, ref_quality = vref
        item = Item(action=action, url=url)

        if hasattr(mod, item.action):
            # Channel specific function to retrieve the sources
            sitems = getattr(mod, item.action)(item)
        else:
            # Generic function to retrieve the sources
            item.action = 'servertools.find_video_items'
            sitems = servertools.find_video_items(item)
    except Exception as ex:
        log.notice('{m}.{f}.get_sources(%s, ...): %s', provider[2], ex)
        return []

    if not sitems:
        log.debug('{m}.{f}.get_sources(%s, ...): no sources found by %s(%s)', provider[2], item.action, item.url)

    sources = {}
    for sitem in sitems:
        if sitem.action != 'play':
            log.debug('{m}.{f}.get_sources(%s, ...): play action not specified for source %s', provider[2], sitem.__dict__)
            continue

        log.debug('{m}.{f}.get_sources(%s, ...): processing source %s', provider[2], sitem.__dict__)

        stitle = sitem.title        

        # Extract the stream quality if provided in the title, otherwise fallback to the quality
        # found in the sources page title but not if 'source_quality_override' is a channel option (e.g. cineblog01)
        quality = 'HD' if re.search(r'[^\w]HD[^\w]', stitle) else \
                  'SD' if _channel_option(provider[2], 'source_quality_override') else \
                  ref_quality

        # Remove known tags and year
        stitle = re.sub(r'\[HD\]', '', stitle)
        stitle = re.sub(r'\(\d{4}\)', '', stitle)

        # Remove the [COLOR ...]<info>[/COLOR] tags and collect the <info>
        info_tags = []
        def collect_color_tags(match):
            tag = match.group(1)
            if tag not in _channel_option(provider[2], 'ignore_tags', []):
                info_tags.append(tag) #pylint: disable=W0640
            return ''

        stitle = re.sub(r'\[COLOR\s+[^\]]+\]([^\[]*)\[/COLOR\]', collect_color_tags, stitle)
        stitle = re.sub(r'\[/?COLOR[^\]]*\]', '', stitle)
        # Extract the host if possible
        try:
            host = re.search(r'\s+-\s+\[([^\]]+)\]', stitle).group(1)
        except Exception:
            try:
                host = re.search(r'\[([^\]]+)\]', stitle).group(1)
            except Exception:
                host = ''
        host = host.split(' ')[-1].translate(None, '@')

        if not hasattr(mod, sitem.action):
            # No channel specific resolver
            url = sitem.url
            action = ''
        else:
            # Channel specific resolver to run first
            try:
                pitems = getattr(mod, sitem.action)(sitem)
            except Exception:
                pitems = []
            if not len(pitems):
                log.debug('{m}.{f}.get_sources(%s, ...): url cannot be resolved for source %s', provider[2], sitem.__dict__)
                continue
            url = pitems[0].url
            action = pitems[0].action

        sources[url] = {
            'source': host,
            'quality': quality,
            'info': ('[%s] '%' '.join(info_tags) if info_tags else '')+title,
            'url': url,
        }

        log.debug('{m}.{f}.get_sources(%s, ...): %s', provider[2], sources[url])

    return sources.values()
