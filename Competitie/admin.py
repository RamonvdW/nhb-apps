# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from .models import Competitie, DeelCompetitie, CompetitieKlasse


admin.site.register(Competitie)
admin.site.register(DeelCompetitie)
admin.site.register(CompetitieKlasse)

# end of file
