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

site = 'github://J0rdyz65/genesi2.packages/contents/italian-isod'
"""
    The :site: attribute is the URL used to fetch the directory content in JSON format from GitHub.
    The 'github://' prefix is a shorthand for 'https://api.github.com/repos/'
"""

addons = ['plugin.video.streamondemand']
"""
    The :addons: attribute is a list of kodi addons identifier whose libraries have to be included
    in the sys.path in order for this package to work. For script.module.* addons the sys.path
    is agumented with the addon ./lib subdirectory while for the other addons the sys.path is
    augmented with the addon main directory.
"""
