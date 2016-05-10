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


from resources.lib import dbs

from resources.lib.libraries import cache
from resources.lib.libraries import uis
from resources.lib.language import _

from resources.lib.uis import movies


info = {
    'methods': ['menu', 'search', 'movielist'],
}


def menu(**kwargs):
    """Sample replacement of the default movies.menu"""
    if dbs.url('movies{title}', title=''):
        uis.addDirectoryItem(_('Search by Title'), 'movies.search', 'movieSearch.jpg', 'DefaultMovies.png')
    if dbs.url('person{name}', name=''):
        uis.addDirectoryItem(_('Search by Person'), 'movies.person', 'moviePerson.jpg', 'DefaultMovies.png')
    if dbs.url('movies{year}', year=''):
        uis.addDirectoryItem(_('Search by Year'), 'movies.year', 'movieYears.jpg', 'DefaultMovies.png')
    if dbs.url('movies{genre_id}', genre_id=''):
        uis.addDirectoryItem(_('Genres'), 'movies.genres', 'movieGenres.jpg', 'DefaultMovies.png')
    uis.endDirectory()


def search(action, **kwargs):
    """Sample replacement of the default movies.search"""
    query = uis.doQuery(_('Title'))
    if query is not None:
        url = dbs.url('movies{title}', title=query)
        movielist(action, url)


def movielist(action, url, **kwargs):
    """Sample replacement of the default movies.movielist"""
    items = cache.get(dbs.movies, 24, url)
    # TODO: signal empty directory (if not items:...)
    for i in items: i['next_action'] = 'movies.movielist'

    # TODO: this should become a uis primitive
    movies._add_movie_directory(action, items)
