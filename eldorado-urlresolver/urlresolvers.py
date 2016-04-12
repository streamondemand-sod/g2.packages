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
import sys

import xbmc


__all__ = ['netloc', 'resolve']


def _netloc():
    import urlresolver

    try:
        _resolvers = urlresolver.plugnplay.man.implementors(urlresolver.UrlResolver)
    except Exception:
        _resolvers = []

    netloc = []
    for r in _resolvers:
        try:
            module = r.fname if isinstance(r, urlresolver.plugnplay.interfaces.UrlWrapper) else re.search(r'<([^\.]+)\.', str(r)).group(1)
            netloc.append({
                'sub_module': module,
                'domains': r.domains,
            })
        except Exception:
            pass
    return netloc


netloc = _netloc() if xbmc.getCondVisibility('System.HasAddon(script.module.urlresolver)') else []


def resolve(module, url):
    import urlresolver

    url = urlresolver.resolve(url)
    if type(url) == bool: url = None

    return url
