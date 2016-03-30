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
import xbmcaddon


if xbmc.getCondVisibility('System.HasAddon(script.module.urlresolver)'):
    # This sys.path modification is required because the addon is NOT included in the addon require section
    sys.path.append(os.path.join(xbmcaddon.Addon('script.module.urlresolver').getAddonInfo('path'), 'lib'))

    try:
        import urlresolver.plugnplay
        resolvers = urlresolver.plugnplay.man.implementors(urlresolver.UrlResolver)
        resolvers = [i for i in resolvers if not '*' in i.domains]
    except:
        resolvers = []

    try:
        netloc = [i.domains for i in resolvers]
        netloc = [i.lower() for i in reduce(lambda x, y: x+y, netloc)]
        netloc = [x for y,x in enumerate(netloc) if x not in netloc[:y]]
    except:
        netloc = []


def resolve(url):
    import urlresolver

    url = urlresolver.resolve(url)
    if type(url) == bool: url = None

    return url
