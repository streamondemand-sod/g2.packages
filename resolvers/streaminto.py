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
    'domains': ['streamin.to'],
}


def resolve(module, url):
    if not url.startswith("http://streamin.to/embed-"):
        code = re.search(r'streamin.to/([a-z0-9A-Z]+)', url).group(1)
        url = 'http://streamin.to/embed-%s.html'%code

    result = client.request(url)

    if 'File was deleted' in result:
        return ResolverError('File was deleted')

    site = re.search(r'image: "(http://[^/]+)', result).group(1)
    path = re.search(r'file: "([^"]+)"', result).group(1).split('=')[1]
    url = '%s/%s/v.flv'%(site, path)

    return url
