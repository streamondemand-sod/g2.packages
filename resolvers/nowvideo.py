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

from g2.libraries import client
from g2.resolvers import ResolverError


info = {
    'domains': ['nowvideo.eu', 'nowvideo.sx', 'nowvideo.li'],
}


def resolve(module, url):
    videoid = re.compile(r'//.+?/.+?/([\w]+)').findall(url)
    videoid += re.compile(r'//.+?/.+?v=([\w]+)').findall(url)
    videoid = videoid[0]

    url = 'http://embed.nowvideo.sx/embed.php?v=%s' % videoid

    result = client.request(url)

    key = re.compile('flashvars.filekey=(.+?);').findall(result)[-1]
    try:
        key = re.compile(r'\s+%s="(.+?)"' % key).findall(result)[-1]
    except Exception:
        pass

    url = 'http://www.nowvideo.sx/api/player.api.php?key=%s&file=%s' % (key, videoid)
    result = client.request(url)

    try:
        # error=1&error_msg=The video no longer exists
        return ResolverError(re.compile('error_msg=(.*)').findall(result)[0])
    except Exception:
        pass

    url = re.compile('url=(.+?)&').findall(result)[0]

    return url
