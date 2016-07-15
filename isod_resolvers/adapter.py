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

import importer

from g2.libraries import log


_SOD_ADDON_SERVERS_PACKAGE = 'servers'

_EXCLUDED_SERVERS = [
    'servertools',      # Not a server
    'longurl',          # Looks like a short url resolver
]


def info(paths):
    from core import logger
    logger.log_enable(False)

    # (fixme) this should be checked against the ISOD default.py module, but, for now,
    # let's have it hardcoded
    paths.append(os.path.join(paths[0], 'lib'))

    nfo = []
    for package, module, is_pkg in importer.walk_packages([os.path.join(paths[0], _SOD_ADDON_SERVERS_PACKAGE)]):
        if is_pkg or module in _EXCLUDED_SERVERS:
            continue
        log.debug('{p}.{f}: from %s import %s (%s)', _SOD_ADDON_SERVERS_PACKAGE, module, type(module))
        try:
            mod = getattr(__import__(_SOD_ADDON_SERVERS_PACKAGE, globals(), locals(), [module], -1), module)
        except Exception as ex:
            log.error('{p}.{f}: from %s import %s: %s', _SOD_ADDON_SERVERS_PACKAGE, module, ex)
            continue
        if not hasattr(mod, 'get_video_url'):
            continue

        source = package.find_module(module).get_source()

        try:
            url_patterns = _fetch_patterns_by_ast(source)
        except Exception as ex:
            log.debug('{m}.{f}: %s: %s', module, repr(ex))
            continue

        if not url_patterns:
            log.debug('{p}.{f}: %s: no url pattern found', module)
        else:
            log.debug('{p}.{f}: %s: url patterns: %s', module, ' | '.join(url_patterns))
            nfo.append({
                'name': module,
                'url_patterns': url_patterns,
            })
    return nfo


def _fetch_patterns_by_ast(source):
    import ast

    pattern_variables = [
        'patronvideos', # most of the others
        'pattern',      # videomega
        'patterns',     # netutv
    ]

    mod_ast = ast.parse(source)
    find_videos = [s for s in mod_ast.body if hasattr(s, 'name') and s.name == 'find_videos'][0]
    patronvideos = [s for s in find_videos.body if hasattr(s, 'targets') and s.targets[0].id in pattern_variables]

    url_patterns = []
    for stmt in patronvideos:
        try:
            patterns = ast.literal_eval(stmt.value)
            if isinstance(patterns, basestring):
                patterns = [patterns]
        except Exception as ex:
            log.notice('{p}.{f}: %s: value cannot be evaluated: %s', ast.dump(stmt.value, annotate_fields=False), repr(ex))

        for pat in patterns:
            try:
                if re.compile(pat):
                    url_patterns.append(pat)
            except Exception as ex:
                log.notice('{p}.{f}: %s: invalid pattern: %s', pat, repr(ex))

    return url_patterns


def resolve(module, url):
    urls = getattr(__import__(_SOD_ADDON_SERVERS_PACKAGE, globals(), locals(), [module[2]], -1), module[2]).get_video_url(url)
    # (fixme) the url resolution might return multiple urls with different stream quality,
    # this should be handled in the resolvers.resolve.
    return None if not urls else urls[0][1]
