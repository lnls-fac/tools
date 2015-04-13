# -*- coding: utf-8  -*-

__version__ = '$Id: 8da907000a48dfa81f05522767b1f1ecb994db8a $'

from pywikibot import family


# The project wiki of OpenStreetMap (OSM).
class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'osm'
        self.langs = {
            'en': 'wiki.openstreetmap.org',
        }

    def version(self, code):
        return "1.22.7"
