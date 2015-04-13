# -*- coding: utf-8  -*-
__version__ = '$Id: a4ec752b802b7f222ebb83c63ef7197fa8fd07be $'

from pywikibot import family


# The LyricWiki family

# user_config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'lyricwiki'
        self.langs = {
            'en': 'lyrics.wikia.com',
        }

    def version(self, code):
        return "1.19.18"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        return '/api.php'
