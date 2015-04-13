# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id: 812da2145504b672eba363c0a739b9e68f39c0d1 $'


# The Wikimedia family that is known as Wikiversity
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikiversity'

        self.languages_by_size = [
            'en', 'fr', 'de', 'beta', 'ru', 'cs', 'it', 'es', 'pt', 'ar', 'fi',
            'sv', 'el', 'sl', 'ko', 'ja',
        ]

        self.langs = dict([(lang, '%s.wikiversity.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ja', ]
