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

from resources.lib.libraries import client


__all__ = ['netloc', 'resolve']


netloc = ['akstream.video']


def resolve(module, url):
    url = url.replace('/videos/', '/stream/')
    
    cookie = [] # Cookies are returned here...
    result = client.request(url, cookie=cookie)

    result = client.parseDOM(result, 'input', attrs={'type': 'hidden', 'name': 'streamLink'}, ret='value')[0]

    result = client.request('http://akstream.video/viewvideo.php', post='streamLink=%s'%result, referer=url, cookie="; ".join(cookie))

    url = client.parseDOM(result, 'source', attrs={'type': 'video/mp4'}, ret='src')[0]

    return url
