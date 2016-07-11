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


_SOD_ADDON_CHANNELS_PACKAGE = 'channels'

_DEFAULT_EXCLUDED_CHANNELS = [
    'corsaronero',      # torrent only
    'mondolunatico',    # fire up a captcha dialog
]

_CHANNELS_OPTIONS = {
    'casacinema': {
        'content': ['movie', 'episode'],
    },
    'cineblog01': {
        'remove_chars': ':',
        'use_year': ' (%s)',
        'source_quality_override': True,
        'ignore_tags': ['Streaming HD:', 'Streaming:'],
        'content': ['movie'], # bad series scraper...
    },
    'cinemalibero': {
        'content': ['movie'], # bad series scraper...
    },
    'darkstream': {
        'content': ['movie'], # bad series scraper...
    },
    'eurostreaminginfo': {
        'content': ['movie'], # bad series scraper...
    },
    'filmpertutti': {
        'content': ['movie', 'episode'],
    },
    'filmsenzalimiti': {
        'content': ['movie'], # bad series scraper...
    },
    'filmstreampw': {
        'content': ['movie'], # bad series scraper...
    },
    'filmstream': {
        'content': ['movie'], # bad series scraper...
    },
    'guardarefilm': {
        'content': ['movie', 'episode'],
    },
    'itafilmtv': {
        'content': ['movie', 'episode'],
    },
    'italiafilm': {
        'content': ['movie', 'episode'],
    },
    'italianstream': {
        'content': ['movie'], # bad series scraper...
    },
    'liberoita': {
        'content': ['movie', 'episode'],
    },
    'piratestreaming': {
        'content': ['movie', 'episode'],
    },
    'solostreaming': {
        'content': ['movie', 'episode'],
    },
    'tantifilm': {
        'content': ['movie', 'episode'],
    },
}


def _channel_option(channel, option, default=None):
    return _CHANNELS_OPTIONS.get(channel, {}).get(option, default)


def info(paths):
    from core import logger
    logger.log_enable(False)

    # (fixme) this should be checked against the ISOD default.py module, but, for now,
    # let's have it hardcoded
    paths.append(os.path.join(paths[0], 'lib'))

    excluded_channels = _DEFAULT_EXCLUDED_CHANNELS
    try:
        sodsearch_path = os.path.join(paths[0], 'resources', 'sodsearch.txt')
        with open(sodsearch_path) as fil:
            excluded_channels.extend(fil.readlines())
    except Exception as ex:
        log.notice('{p}: %s: %s', sodsearch_path, repr(ex))
    excluded_channels = [ec.strip() for ec in excluded_channels if ec.strip()]

    nfo = []
    for dummy_package, channel, is_pkg in importer.walk_packages([os.path.join(paths[0], _SOD_ADDON_CHANNELS_PACKAGE)]):
        if is_pkg or channel in excluded_channels:
            continue
        try:
            mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [channel], -1), channel)
        except Exception as ex:
            log.error('{m}.{f}: from %s import %s: %s', _SOD_ADDON_CHANNELS_PACKAGE, channel, ex)
            continue
        if hasattr(mod, 'search'):
            nfo.append({
                'name': channel,
                'content': _channel_option(channel, 'content', ['movie']),
            })

    log.notice('{p}: %d channels found', len(nfo))

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

    for i in items:
        for tag in ['streaming', 'ita']:
            i.fulltitle = re.sub(r'(?i)(^|[^\w])%s([^\w]|$)'%tag, r'\1\2', i.fulltitle)

    return [(i.url, i.fulltitle, i.action, 'HD' if re.search(r'[^\w]HD[^\w]', i.fulltitle) else 'SD') for i in items]


def get_episode(provider, tvshowtitle, season, episode, **kwargs):
    from servers import servertools
    from core.item import Item

    try:
        mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [provider[2]], -1), provider[2])
    except Exception as ex:
        log.error('{m}.{f}.get_episode(%s, ...): %s', provider[2], ex)
        return None

    try:
        if _channel_option(provider[2], 'remove_chars'):
            tvshowtitle = tvshowtitle.translate(None, _channel_option(provider[2], 'remove_chars'))
        search_terms = unidecode(tvshowtitle)
        item = Item()
        item.extra = 'serie'

        items = mod.search(item, urllib.quote_plus(search_terms))
        if not items:
            return None
    except Exception as ex:
        log.notice('{m}.{f}.get_episode(%s, %s, ...): %s', provider[2], tvshowtitle, ex)
        return None

    for i in items:
        for tag in ['streaming', 'ita', 'serie', 'tv']:
            i.fulltitle = re.sub(r'(?i)(^|[^\w])%s([^\w]|$)'%tag, r'\1\2', i.fulltitle)

    return [(i.url, i.fulltitle.strip(), i.action, 'HD' if re.search(r'[^\w]HD[^\w]', i.fulltitle) else 'SD', season, episode)
            for i in items]


def get_sources(provider, vref):
    from servers import servertools
    from core.item import Item

    try:
        mod = getattr(__import__(_SOD_ADDON_CHANNELS_PACKAGE, globals(), locals(), [provider[2]], -1), provider[2])

        season = None
        episode = None
        if len(vref) == 4:
            url, title, action, ref_quality = vref
        elif len(vref) == 6:
            url, title, action, ref_quality, season, episode = vref
        else:
            log.notice('{m}.{f}.%s: expected 4 or 6 vref elements, found %d', provider[2], len(vref))
            return []

        item = Item(action=action, url=url)

        if hasattr(mod, item.action):
            # Channel specific function to retrieve the sources
            sitems = getattr(mod, item.action)(item)
        else:
            # Generic function to retrieve the sources
            item.action = 'servertools.find_video_items'
            sitems = servertools.find_video_items(item)
    except Exception as ex:
        log.notice('{m}.{f}.%s: %s', provider[2], repr(ex))
        return []

    if not sitems:
        log.debug('{m}.{f}.%s: no sources found by %s(%s)', provider[2], item.action, item.url)

    nitems = []
    for i in sitems:
        if i.action == 'play':
            nitems.append(i)
        elif hasattr(mod, i.action):
            try:
                nis = getattr(mod, i.action)(i)
                if nis:
                    nitems.extend(nis)
            except Exception as ex:
                log.notice('{m}.{f}.%s: %s: %s', provider[2], i.action, repr(ex))
    sitems = nitems

    sources = {}
    for sitem in sitems:
        if sitem.action != 'play':
            log.debug('{m}.{f}.%s: play action not specified for source %s', provider[2], sitem.__dict__)
            continue

        log.debug('{m}.{f}.%s: processing source %s', provider[2], sitem.__dict__)

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
            tag = match.group(1).strip()
            if tag and tag not in _channel_option(provider[2], 'ignore_tags', []):
                info_tags.append(tag.decode('utf-8'))
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
                log.debug('{m}.{f}.%s: url cannot be resolved for source %s', provider[2], sitem.__dict__)
                continue
            url = pitems[0].url
            action = pitems[0].action

        sitem.title = sitem.title.decode('utf-8').strip()
        sitem.fulltitle = sitem.fulltitle.decode('utf-8').strip()
        if not info_tags:
            info_tags = [sitem.title, sitem.fulltitle]

        source = {
            'url': url,
            'source': host,
            'quality': quality,
            'info': ('[%s] '%' '.join(info_tags) if info_tags else '') + title,
        }

        # (fixme): filter SUB ITA vs ITA

        if season and episode:
            for nfo in [source['info'], sitem.title, sitem.fulltitle]:
                match = re.search(r'[^\d]?(\d)x(\d{1,2})[^\d]', unidecode(nfo))
                if match:
                    break
            source.update({
                'season': '0' if not match else str(int(match.group(1))),
                'episode': '0' if not match else str(int(match.group(2))),
                })

        sources[url] = source

        log.debug('{m}.{f}.%s: %s', provider[2], sources[url])

    return sources.values()
