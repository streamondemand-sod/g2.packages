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
import urlparse

from g2.libraries import client
from .lib import jsunpack


info = {
    'domains': ['videomega.tv'],
}


def resolve(module, url):
    url = urlparse.urlparse(url).query
    url = urlparse.parse_qsl(url)[0][1]
    url = 'http://videomega.tv/cdn.php?ref=%s' % url

    result = client.request(url, mobile=True)
    if jsunpack.detect(result):
        result = re.search(r'(eval.function.p,a,c,k,e,.*?)\s*</script>', result).group(1)
        result = jsunpack.unpack(result)
        url = re.search(r'"src"\s*,\s*"([^"]+)', result).group(1)
    else:
        url = client.parseDOM(result, 'source', ret='src', attrs={'type': 'video.+?'})[0]

    return url
