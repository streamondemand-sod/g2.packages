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


if xbmc.getCondVisibility('System.HasAddon(script.module.urlresolver)'):
    import urlresolver

    try:
        _resolvers = urlresolver.plugnplay.man.implementors(urlresolver.UrlResolver)
        _resolvers = [i for i in _resolvers if not '*' in i.domains]
    except:
        _resolvers = []

    try:
        netloc = [i.domains for i in _resolvers]
        netloc = [i.lower() for i in reduce(lambda x, y: x+y, netloc)]
        netloc = [x for y,x in enumerate(netloc) if x not in netloc[:y]]
    except:
        netloc = []


def resolve(module, url):
    url = urlresolver.resolve(url)
    if type(url) == bool: url = None

    return url
