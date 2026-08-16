# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from .import_geo import ImportCrmGeo
from .import_spelden import ImportCrmSpelden
from .import_functies import ImportCrmFuncties
from .import_sporters import ImportCrmSporters
from .import_locaties import ImportCrmLocaties
from .import_opleidingen import ImportCrmOpleidingen
from .import_verenigingen import ImportCrmVerenigingen

__all__ = [
    'ImportCrmGeo',
    'ImportCrmSpelden',
    'ImportCrmFuncties',
    'ImportCrmSporters',
    'ImportCrmLocaties',
    'ImportCrmOpleidingen',
    'ImportCrmVerenigingen',
]


# end of file
