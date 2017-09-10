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
from g2.libraries import client


info = {
    'domains': ['rai.it'],
}

_BASE_URL = "http://www.rai.it"


def resolve(dummy_module, url):
    with client.Session() as session:
        video = session.get(url).json()
        if not video.get('pathFirstItem'):
            return None
        video = session.get(_BASE_URL+video['pathFirstItem']).json()
        return None if not video.get('video') else video['video'].get('contentUrl')
