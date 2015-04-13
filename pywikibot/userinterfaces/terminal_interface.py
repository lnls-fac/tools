# -*- coding: utf-8 -*-
#
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: 6805138e4d61d263efdcc983face9e9637ee240b $'

import sys

if sys.platform == 'win32':
    from .terminal_interface_win32 import Win32UI as UI
else:
    from .terminal_interface_unix import UnixUI as UI

__all__ = ['UI']
