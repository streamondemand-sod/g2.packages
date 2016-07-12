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
from g2.libraries import client

from .lib import jsunpack


_BASE_URL = 'http://www.cb01.co'
_SEARCH_MOVIE_QUERY = '/?s=%s'
_SEARCH_TVSHOW_QUERY = '/serietv/?s=%s'


def get_movie(dummy_module, title, year='0', **dummy_kwargs):
    # cb01 search module doesn't like the semicolons in the titles
    title = unidecode(title).translate(None, ':')

    try:
        year = int(year)
    except Exception:
        year = 0

    # (fixme) alternative is to use year only when the title is a single word...
    items = _do_search(_SEARCH_MOVIE_QUERY, title, year)
    if not items and year:
        items = _do_search(_SEARCH_MOVIE_QUERY, title, year-1)

    return items


def get_episode(dummy_module, tvshowtitle, season, episode, **dummy_kwargs):
    # cb01 search module doesn't like the semicolons in the titles
    tvshowtitle = unidecode(tvshowtitle).translate(None, ':')

    items = _do_search(_SEARCH_TVSHOW_QUERY, tvshowtitle)
    for i in range(len(items)):
        items[i] += (season, episode,)

    return items


def _do_search(query, title, year=None):
    query = query % urllib.quote_plus('%s (%s)' % (title, year) if year else title)
    query = urlparse.urljoin(_BASE_URL, query)

    result = _cloudflare(query)

    result = result.decode('iso-8859-1').encode('utf-8')
    result = client.parseDOM(result, 'div', attrs={'class': 'span12 filmbox'})
    result = [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'h1')[0]) for i in result]
    result = [(u, unidecode(client.replaceHTMLCodes(t))) for u, t in result]

    return [i for i in result
            if not re.search(r'\(\d{4}\)', i[1])
            or any(x in i[1] for x in ['(%s)'%str(y) for y in range(year-1, year+2)])]


def get_sources(dummy_module, vref):
    if len(vref) == 2:
        return _get_movie_sources(*vref)
    elif len(vref) == 4:
        return _get_episode_sources(*vref)
    else:
        return []


def _get_movie_sources(url, title):
    result = client.request(url).content
    result = client.parseDOM(result, 'table', attrs={})
    result = [t for t in result if 'Streaming:' in t][0]
    result = client.parseDOM(result, 'td', attrs={})
    result = reduce(lambda x, y: x+y, [client.parseDOM(t, 'td', attrs={}) for t in result], [])

    sources = []
    quality = 'SD'
    sources_area = False
    info = []
    for tdi in result:
        if 'Streaming' in tdi:
            sources_area = True
            if 'HD' in tdi:
                quality = 'HD'

        elif 'Download' in tdi:
            sources_area = False

        else:
            try:
                divs = client.parseDOM(tdi, 'div', attrs={'align': 'right'})
                if divs:
                    nfo = client.parseDOM(divs[0], 'strong')[0]
                    nfo = re.sub(r'<a.*?</a>', '', nfo)
                    info.append(unidecode(client.replaceHTMLCodes(nfo)).strip())

                elif sources_area:
                    url = client.parseDOM(tdi, 'a', ret='href')[0]
                    host = client.parseDOM(tdi, 'a')[0]
                    sources.append({
                        'source': unidecode(client.replaceHTMLCodes(host)),
                        'quality': quality,
                        'url': url,
                    })
            except Exception:
                pass

    for src in sources:
        src['info'] = ('' if not info else '[%s] '%(' '.join(info))) + title

    return sources


def _get_episode_sources(url, tvshowtitle, season, episode):
    result = client.request(url).content
    sources = []

    # Season container:
    # <div class="sp-wrap sp-wrap-default">
    for season_dom in client.parseDOM(result, 'div', attrs={'class': 'sp-wrap sp-wrap-default'}):
        # Season header:
        # <div class="sp-head unfolded" title="Collapse">
        # STAGIONE 1 - ITA - HDTVMux - NovaRip
        # </div>
        try:
            nfo = client.parseDOM(season_dom, 'div', attrs={'class': 'sp-head.*?'})[0].strip()
        except Exception:
            nfo = ''

        if 'SUB' in nfo:
            log.debug('{m}.{f}: %s: discarded because SUB filter not implemented yet', nfo)
            continue

        quality = 'HD' if 'HD' in nfo else 'SD'
        nfo = [nfo] if nfo else []

        # Episode container:
        # <p>1×01 L inverno sta arrivando ...
        #   <a href="http://swzz.xyz/link/n4kZK/" target="_blank">Rockfile</a>
        #   ...
        # </p>
        for episode_dom in client.parseDOM(season_dom, 'p'):
            episode_dom = client.replaceHTMLCodes(episode_dom)
            episode_dom = episode_dom.replace('<strong>', '')
            episode_dom = episode_dom.replace('</strong>', '')

            # Match the season x episode title
            match = re.search(r'(?:^|[^\d])(\d{1,2})x(\d{1,2})\s+?([^-<]*)', unidecode(episode_dom), re.S)
            if not match:
                continue

            e_season = str(int(match.group(1)))
            e_episode = str(int(match.group(2)))
            e_nfo = match.group(3).strip()
            e_nfo = [e_nfo] if e_nfo else []

            s_quality = quality
            s_nfo = e_nfo
            while True:
                episode_dom = episode_dom[match.end():]

                # Match the quality and rip tool, if present
                match = re.match(r'[^\w<]*?([\w\s]+?):', episode_dom)
                if match and match.group(1).strip():
                    s_nfo = e_nfo + [match.group(1).strip()]
                    s_quality = 'HD' if 'HD' in s_nfo[-1] else 'SD'

                # Match the url and host source
                match = re.search(r'<a\s+?href\s*?=\s*?"([^"]+)".*?>([^<]+)</a>', episode_dom)
                if not match:
                    break
                url = match.group(1)
                host = match.group(2).strip()
                sources.append({
                    'url': url,
                    'source': unidecode(host),
                    'quality': s_quality,
                    'info': ' / '.join(s_nfo + nfo),
                    'season': e_season,
                    'episode': e_episode,
                })

            # urls = client.parseDOM(episode_dom, 'a', ret='href')
            # hosts = client.parseDOM(episode_dom, 'a')
            # for url, host in zip(urls, hosts):
            #     sources.append({
            #         'url': url,
            #         'source': unidecode(host),
            #         'quality': quality,
            #         'info': ' '.join([s_nfo, nfo]),
            #         'season': s_season,
            #         'episode': s_episode,
            #     })

    return sources


def resolve(dummy_module, url):
    result = client.request(url).content if not 'go.php' in url else _cloudflare(url)

    scripts = client.parseDOM(result, 'script')
    rurl = None
    for i in scripts:
        match = re.search(r'(eval\(function\(p,a,c,k,e,d.*)', i)
        if match:
            i = jsunpack.unpack(match.group(1))

        match = re.search(r'var link\s*=\s*"([^"]+)";', i)
        if match:
            rurl = match.group(1)
            break

        match = re.search('window.location.href = "([^"]+)";', i)
        if match:
            rurl = match.group(1)
            break

    if not rurl:
        rurl = client.parseDOM(result, 'a', attrs={'class': 'btn-wrapper'}, ret='href')[0]

    return rurl


def _cloudflare(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0',
    }

    with client.Session(debug=log.debugactive()) as session:
        res = session.request(url, headers=headers)

        if 'refresh' in res.headers:
            # refresh=8;URL=/cdn-cgi/l/chk_jschl?pass=1457690427.305-qGo9Ho8gdZ
            refresh_timeout = int(res.headers['refresh'][:1])
            refresh_url = res.headers['refresh'][6:]
            time.sleep(refresh_timeout)
            session.request(urlparse.urljoin(_BASE_URL, refresh_url), headers=headers)

        elif '"challenge-form"' in res.content:
            base_url = '%s://%s' % (urlparse.urlparse(url).scheme, urlparse.urlparse(url).netloc)
            jschl_vc = re.compile(r'name="jschl_vc" value="(.+?)"').findall(res.content)[0]
            init_val = re.compile(r'setTimeout\(function\(\).*?:(.+?)};', re.S).findall(res.content)[0]
            builder = re.compile(r"challenge-form'\);\s*(.*)a.value", re.S).findall(res.content)[0]
            decrypted_val = _parseJSString(init_val)
            for line in builder.split(';'):
                expr = line.split('=')
                if len(expr) < 2:
                    continue
                line_val = _parseJSString(expr[1])
                expr_val = str(decrypted_val) + expr[0][-1] + str(line_val)
                log.debug('{m}.{f}: %s', expr_val)
                decrypted_val = eval(expr_val)
                log.debug('{m}.{f}: %s: %d', expr_val, decrypted_val)

            answer = decrypted_val + len(urlparse.urlparse(url).netloc)
            query = '%s/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % (base_url, jschl_vc, answer)

            if 'type="hidden" name="pass"' in res.content:
                pass_val = re.compile(r'name="pass" value="(.*?)"').findall(res.content)[0]
                query = '%s/cdn-cgi/l/chk_jschl?pass=%s&jschl_vc=%s&jschl_answer=%s' % (
                    base_url, urllib.quote_plus(pass_val), jschl_vc, answer)
                time.sleep(5)

            session.request(query, headers=headers)

        return session.request(url, headers=headers).content


def _parseJSString(string):
    try:
        offset = 1 if string[0] == '+' else 0
        expr_val = string.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').replace('(', 'str(')[offset:]
        log.debug('{m}.{f}: %s: %s', string[offset:], expr_val)
        return int(eval(expr_val))
    except Exception:
        return 0
