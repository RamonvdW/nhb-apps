# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

# all klassen zijn hard-coded
# zie migrations/002_basistypen_2019
#TIJDELIJK:
from .models import BoogType, TeamType, WedstrijdKlasse, LeeftijdsKlasse, TeamTypeBoog, WedstrijdKlasseBoog, WedstrijdKlasseLeeftijd

admin.site.register(BoogType)
admin.site.register(TeamType)
admin.site.register(WedstrijdKlasse)
admin.site.register(LeeftijdsKlasse)
admin.site.register(TeamTypeBoog)
admin.site.register(WedstrijdKlasseBoog)
admin.site.register(WedstrijdKlasseLeeftijd)

# end of file
