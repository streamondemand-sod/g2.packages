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
from g2.libraries import client


_SOD_ADDON_SERVERS_PACKAGE = 'servers'

_DEFAULT_EXCLUDED_SERVERS = []


def info(paths):
    from core import logger
    logger.log_enable(False)

    # (fixme) this should be checked against the ISOD default.py module, but, for now,
    # let's have it hardcoded
    paths.append(os.path.join(paths[0], 'lib'))

    active_servers = {}
    servers_dir = os.path.join(paths[0], 'servers')
    for server in os.listdir(servers_dir):
        if os.path.basename(server) in _DEFAULT_EXCLUDED_SERVERS or \
           os.path.splitext(server)[1] != '.xml' or \
           not os.path.isfile(os.path.join(servers_dir, os.path.splitext(server)[0]+'.py')):
            continue
        with open(os.path.join(servers_dir, server)) as fil:
            xml = fil.read()
            active = client.parseDOM(xml, 'active')
            if not active or active[0].lower() != 'true':
                continue
            patterns = client.parseDOM(xml, 'patterns')
            server = os.path.splitext(server)[0]
            for pattern in patterns:
                pattern = client.parseDOM(pattern, 'pattern')
                for pat in pattern:
                    if pat:
                        try:
                            active_servers[server].append(pat)
                        except Exception:
                            active_servers[server] = [pat]

    nfo = []
    for dummy_package, module, is_pkg in importer.walk_packages([os.path.join(paths[0], _SOD_ADDON_SERVERS_PACKAGE)]):
        if is_pkg:
            continue
        if not active_servers.get(module):
            log.debug('{p}.{f}: server %s not active or url patterns not found')
            continue

        log.debug('{p}.{f}: from %s import %s', _SOD_ADDON_SERVERS_PACKAGE, module)
        try:
            mod = getattr(__import__(_SOD_ADDON_SERVERS_PACKAGE, globals(), locals(), [module], -1), module)
        except Exception as ex:
            log.error('{p}.{f}: from %s import %s: %s', _SOD_ADDON_SERVERS_PACKAGE, module, ex)
            continue
        if not hasattr(mod, 'get_video_url'):
            log.debug('{p}.{f}: server %s without get_video_url function')
            continue

        log.debug('{p}.{f}: %s: url patterns: %s', module, ' | '.join(active_servers[module]))
        nfo.append({
            'name': module,
            'url_patterns': active_servers[module],
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
    find_videos = [o for o in mod_ast.body if hasattr(o, 'name') and o.name == 'find_videos'][0]
    patronvideos = [o for o in ast.walk(find_videos)
                    if hasattr(o, 'targets') and hasattr(o.targets[0], 'id') and o.targets[0].id in pattern_variables]

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
    if not urls:
        return None

    # (fixme) the url resolution might return multiple urls with different stream quality,
    # this should be handled in the resolvers.resolve.
    for url in urls:
        log.debug('{m}.{f}: %s', url)

    return urls[-1][1]
