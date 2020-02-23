# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin

from .models import HistCompetitie, HistCompetitieIndividueel, HistCompetitieTeam

admin.site.register(HistCompetitie)
admin.site.register(HistCompetitieIndividueel)
admin.site.register(HistCompetitieTeam)

# end of file
