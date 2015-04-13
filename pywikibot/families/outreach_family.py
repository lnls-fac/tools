# -*- coding: utf-8  -*-

__version__ = '$Id: 3e112843d1fa41d4b3e943820625a2e043340ea9 $'

from pywikibot import family


# Outreach wiki custom family
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = u'outreach'
        self.langs = {
            'outreach': 'outreach.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
