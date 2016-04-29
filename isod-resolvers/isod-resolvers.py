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

from resources.lib import resolvers


__all__ = ['netloc', 'resolve']


_sod_addon_servers_package = 'servers'
_sod_addon_servers_path = os.path.join(xbmcaddon.Addon('plugin.video.streamondemand').getAddonInfo('path'), _sod_addon_servers_package)
_excluded_servers = [
    'servertools',      # Not a server
    'longurl',          # Looks like a short url resolver
]


def _netloc():
    from core import logger
    logger.log_enable(False)

    netloc = []
    for package, module, is_pkg in importer.walk_packages([_sod_addon_servers_path]):
        if is_pkg or module in _excluded_servers: continue
        try:
            m = getattr(__import__(_sod_addon_servers_package, globals(), locals(), [module], -1), module)
        except Exception as e:
            log.notice('isod-resolvers: from %s import %s: %s'%(_sod_addon_servers_package, module, e))
            continue
        if not hasattr(m, 'get_video_url'): continue

        source = package.find_module(module).get_source()
        url_patterns = []
        #
        # The regular expressions matching the handled urls are found in the following statements:
        #   patronvideos = 'http://abysstream.com/videos/([A-Za-z0-9]+)'
        #
        for match in re.finditer(r'patronvideos\s*=\s*u?r?("""|\'\'\'|"|\')((?:\\\1|.)*?)\1', source):
            pat = match.group(2)
            try:
                if re.compile(pat):
                    url_patterns.append(pat)
            except Exception as e:
                log.notice('isod-resolvers: %s: invalid pattern: %s'%(pat, e))

        if not url_patterns:
            log.debug('isod-resolvers: %s: no url pattern found'%module)
        else:
            log.debug('isod-resolvers: %s: url patterns: %s'%(module, ' | '.join(url_patterns)))
            netloc.append({
                'sub_module': module,
                'url_patterns': url_patterns,
            })
    return netloc


netloc = _netloc()


def resolve(module, url):
    urls = getattr(__import__(_sod_addon_servers_package, globals(), locals(), [module[2]], -1), module[2]).get_video_url(url)

    return None if not urls else urls[0][1]