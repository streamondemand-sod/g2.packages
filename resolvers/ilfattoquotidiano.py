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


from g2.libraries import log
from g2.libraries import client2


info = {
    'domains': ['ilfattoquotidiano.it'],
}


def resolve(module, url):
    # res = Util.getResponseBS(url)
    res = client2.get(url, bs_body=True)

    video = res.bs_body.find('video', {'id' : 'bcPlayer'})
    log.notice('{m}.{f}: VIDEO=%s', video)

    url = 'https://edge.api.brightcove.com/playback/v1/accounts/{data_account}/videos/{data_video_id}'.format(
        data_account=video['data-account'],
        data_video_id=video['data-video-id'],
    )
    headers = {
        'Accept': 'application/json;pk=BCpkADawqM0xNxj2Rs11iwmFoNJoG2nXUQs67brI7oR2qm0Dwn__kPcbvLJb7M34IY2ar-WxWvi8wHr6cRbP7nmgilWaDrqZEeQm4O5K6z6B2A3afiPFbv7T4LcsQKN2PqIIgIIr3AXq43vL',
    }
    res = client2.get(url, headers=headers).json()

    # Filter out the sources without src link
    sources = sorted(res['sources'], key=lambda i: i.get('avg_bitrate', 0)*(1 if i.get('src') else 0), reverse=True)
    for src in sources:
        log.notice('{m}.{f}: SOURCE=%s', src)

    return sources[0]['src']
