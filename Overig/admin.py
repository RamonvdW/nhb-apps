# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from .models import SiteFeedback, SiteTijdelijkeUrl

admin.site.register(SiteFeedback)
admin.site.register(SiteTijdelijkeUrl)

# end of file
