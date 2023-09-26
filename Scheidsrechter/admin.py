# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Scheidsrechter.models import ScheidsBeschikbaarheid, WedstrijdDagScheids


admin.site.register(ScheidsBeschikbaarheid)
admin.site.register(WedstrijdDagScheids)

# end of file
