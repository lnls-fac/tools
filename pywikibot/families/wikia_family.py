# -*- coding: utf-8  -*-

__version__ = '$Id: 75a699f9f5551d5bc1d1d3b5041b42ef693ee4e8 $'

from pywikibot import family


# The Wikia Search family
# user-config.py: usernames['wikia']['wikia'] = 'User name'
class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = u'wikia'

        self.langs = {
            u'wikia': None,
        }

    def hostname(self, code):
        return u'www.wikia.com'

    def version(self, code):
        return "1.19.18"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        return '/api.php'
