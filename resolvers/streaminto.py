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


netloc = ['streamin.to']


def resolve(url):
    if not url.startswith("http://streamin.to/embed-"):
        code = re.search(r'streamin.to/([a-z0-9A-Z]+)', url).group(1)
        url = 'http://streamin.to/embed-%s.html'%code

    result = client.request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'})

    if 'File was deleted' in result: return ResolverError('File was deleted')

    site = re.search(r'image: "(http://[^/]+)', result).group(1)
    path = re.search(r'file: "([^"]+)"', result).group(1).split('=')[1]
    url = '%s/%s/v.flv'%(site, path)

    return url
