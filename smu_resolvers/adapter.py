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


import re

import urlresolver

from g2.libraries import log


def info(dummy_paths):
    try:
        resolvers = urlresolver.relevant_resolvers(include_universal=True, include_external=True)
        # resolvers = urlresolver.plugnplay.man.implementors(urlresolver.UrlResolver)
    except Exception as ex:
        log.error('{p}.{f}: %s', repr(ex))
        return []

    nfo = []
    for res in resolvers:
        nfo.append({
            'name': res.name,
            'domains': res.domains,
        })
        log.debug('{p}.{f}: resolver %s: %s', res.name, res.domains)

    return nfo


def resolve(dummy_module, url):
    url = urlresolver.resolve(url)
    if type(url) == bool:
        url = None

    return url
