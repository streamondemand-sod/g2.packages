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

import re

from resources.lib.libraries import client

from lib import jsunpack


netloc = ['flashx.tv']


def resolve(url):
    code = re.search(r'flashx.tv/([a-zA-Z0-9]+)', url).group(1)
    url = 'http://www.flashx.pw/fxplaynew-%s.html'%code
    result = client.request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0'})
    result = client.parseDOM(result, 'script', attrs={'type': 'text/javascript'})
    for i in result:
        if jsunpack.detect(i):
            result = jsunpack.unpack(i)
            result = re.search(r'{sources:\[([^\]]+)\]', result).group(1)
            result = re.compile(r'file:"([^"]+)"').findall(result)[0]
            return result

    return None
