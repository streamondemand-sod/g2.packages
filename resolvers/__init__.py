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

site = 'github://J0rdyz65/genesi2.packages/contents/resolvers'
"""
    The :site: attribute is the URL used to fetch the directory content in JSON format from GitHub.
    The 'github://' prefix is a shorthand for 'https://api.github.com/repos/'
"""

settings = 'addon://'
"""
    The :settings: attribute is the path to the file to monitor to invalidate the modules' cache.
    The addon://PLUGINID filename is translated into the addon settings.xml file found under
    the special://userdata/addon_data/PLUGINID directory. If the PLIGINID is missing, it is
    used the current addon id. Any other filename is taken as is.
"""
