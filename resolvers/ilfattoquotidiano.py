# -*- coding: utf-8 -*-

"""
    G2 Add-on Package
    Thanks to NeverWise
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


from g2.libraries import log
from g2.libraries import client2


_log_debug = True

info = {
    'domains': ['ilfattoquotidiano.it'],
}


def resolve(module, url):
    res = client2.get(url)

    video = client2.parseDOM(res.content, 'video', attrs={'id':'bcPlayer'}, ret=['data-account', 'data-video-id'])[0]

    url = 'https://edge.api.brightcove.com/playback/v1/accounts/{data_account}/videos/{data_video_id}'.format(
        data_account=video['data-account'][0],
        data_video_id=video['data-video-id'][0],
    )
    headers = {
        'Accept': 'application/json;pk=BCpkADawqM0xNxj2Rs11iwmFoNJoG2nXUQs67brI7oR2qm0Dwn__kPcbvLJb7M34IY2ar-WxWvi8wHr6cRbP7nmgilWaDrqZEeQm4O5K6z6B2A3afiPFbv7T4LcsQKN2PqIIgIIr3AXq43vL',
    }
    res = client2.get(url, headers=headers).json()

    # Filter out the sources without src link
    sources = sorted(res['sources'], key=lambda i: i.get('avg_bitrate', 0)*(1 if i.get('src') else 0), reverse=True)
    for src in sources:
        log.debug('{m}.{f}: SOURCE=%s', src)

    return sources[0]['src']
