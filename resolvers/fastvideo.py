# -*- coding: utf-8 -*-

"""
    G2 Add-on Package
    Copyright (C) 2015 lambda

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

from .lib import jsunpack


info = {
    'domains': ['fastvideo.in', 'fastvideo.me', 'faststream.in', 'rapidvideo.ws'],
}


def resolve(module, url):
    rurl = url.replace('/embed-', '/')
    rurl = re.compile(r'//.+?/([\w]+)').findall(rurl)[0]
    rurl = 'http://rapidvideo.ws/embed-%s.html' % rurl

    result = client.request(rurl, mobile=True)

    if 'File was deleted' in result:
        return ResolverError('File was deleted')

    if not jsunpack.detect(result):
        return None

    result = re.compile(r'(eval.*?\)\)\))').findall(result)[-1]
    result = jsunpack.unpack(result)

    url = client.parseDOM(result, 'embed', ret='src')
    url += re.compile("file *: *[\'|\"](.+?)[\'|\"]").findall(result)
    url = [i for i in url if not i.endswith('.srt')]
    url = 'http://' + url[0].split('://', 1)[-1]

    return url
