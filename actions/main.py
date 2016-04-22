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


from resources.lib.actions import addDirectoryItem, endDirectory
from resources.lib.language import _


actions = ['movies']


def movies(**kwargs):
    """Replacement of the main.movies navigation"""
    addDirectoryItem(_('Search by Title'), 'movieSearch', 'movieSearch.jpg', 'DefaultMovies.png')
    addDirectoryItem(30034, 'moviePerson', 'moviePerson.jpg', 'DefaultMovies.png')
    addDirectoryItem(30021, 'movieGenres', 'movieGenres.jpg', 'DefaultMovies.png')
    addDirectoryItem(30022, 'movieYears', 'movieYears.jpg', 'DefaultMovies.png')
    addDirectoryItem(30025, 'movies&url=featured', 'movies.jpg', 'DefaultRecentlyAddedMovies.png')
    addDirectoryItem(30026, 'movies&url=trending', 'moviesTrending.jpg', 'DefaultRecentlyAddedMovies.png')
    addDirectoryItem(30027, 'movies&url=popular', 'moviesPopular.jpg', 'DefaultMovies.png')
    addDirectoryItem(30028, 'movies&url=views', 'moviesViews.jpg', 'DefaultMovies.png')
    addDirectoryItem(30029, 'movies&url=boxoffice', 'moviesBoxoffice.jpg', 'DefaultMovies.png')
    addDirectoryItem(30030, 'movies&url=oscars', 'moviesOscars.jpg', 'DefaultMovies.png')
    addDirectoryItem(30031, 'movies&url=theaters', 'moviesTheaters.jpg', 'DefaultRecentlyAddedMovies.png')
    addDirectoryItem(30032, 'movies&url=added', 'moviesAdded.jpg', 'DefaultRecentlyAddedMovies.png')
    endDirectory()
