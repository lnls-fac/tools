# -*- coding: utf-8  -*-

__version__ = '$Id: 74e6cfd31a8d2b9e422109c68f93c073631b3e47 $'

from pywikibot import family


# Omegawiki, the Ultimate online dictionary
class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'omegawiki'
        self.langs['omegawiki'] = 'www.omegawiki.org'

        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = list(self.langs.keys())

    def hostname(self, code):
        return 'www.omegawiki.org'

    def version(self, code):
        return "1.22.6"

    def scriptpath(self, code):
        return ''

    def path(self, code):
        return '/index.php'

    def apipath(self, code):
        return '/api.php'
