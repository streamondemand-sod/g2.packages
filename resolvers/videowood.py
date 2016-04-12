# -*- coding: utf-8 -*-

"""
    Genesi2 Add-on
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
from lib import unpackerjs3


__all__ = ['netloc', 'resolve']


netloc = ['videowood.tv']


def resolve(module, url):
    result = client.request(url.replace('/video/', '/embed/'), output='response', error=True)
    
    if 'HTTP Error' in result[0]: return ResolverError(result[0])
    if 'video is not ready yet' in result[1]: return ResolverError('Video is not ready yet')

    scripts = client.parseDOM(result[1], 'script')
    for i in scripts:
        match = re.search('(eval\(function\(p,a,c,k,e,d.*)', i)
        if match:
            result = unpackerjs3.unpackjs(match.group(1))
            match = re.search(r'"file"\s*:\s*"([^"]+/video/[^"]+)', result, re.DOTALL)
            if match: return match.group(1)

    return None
