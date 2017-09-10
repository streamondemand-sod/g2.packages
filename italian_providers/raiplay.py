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
import time
import urllib
import urlparse
import unidecode

from unidecode import unidecode

from g2.libraries import log
from g2.libraries import cache
from g2.libraries import client

from ..lib.fuzzywuzzy import fuzz


_BASE_URL = "http://www.rai.it"
# From http://www.raiplay.it/mobile/prod/config/RaiPlay_Config.json
_AZ_TVSHOW_PATH = "/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json"


def get_movie(dummy_module, title, year='0', **dummy_kwargs):

    # cb01 search module doesn't like the semicolons in the titles
    title = unidecode(title)

    try:
        year = int(year)
    except Exception:
        year = 0

    items = []
    try:
        videos = cache.get(_get_raiplay_videos, 24*60)
        items = [(i.get('PathID'), i.get('name'), i.get('PLRanno'), '/'.join(i.get('channel', [])))
                 for i in videos[title[0].upper()]
                 if i.get('tipology') == 'Film'
                 and i.get('PathID')
                 and fuzz.token_sort_ratio(i.get('name'), title) >= 80]
    except Exception as ex:
        log.debug('{m}.{f}: %s', ex)

    log.debug('{m}.{f}: items=%s', items)

    return items


def _get_raiplay_videos():
    with client.Session() as session:
        return session.get(_BASE_URL+_AZ_TVSHOW_PATH).json()


def get_sources(dummy_module, vref):
    return [{
        'source': 'raiplay',
        'quality': 'SD',
        'url': vref[0],
        'info': vref[3]}]
