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

from resources.lib.libraries import client
from resources.lib.resolvers import ResolverError


__all__ = ['netloc', 'resolve']


netloc = ['backin.net']


def resolve(module, url):
    r = client.request(url, output='response', error=True)

    if 'HTTP Error' in r[0]: return ResolverError(r[0])

    return re.search(r'window.pddurl="([^"]+)"', r[1]).group(1)
