# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.admin.apps import AdminConfig


class BeheerConfig(AdminConfig):
    # vervanger voor de default admin site
    default_site = 'Beheer.views.BeheerAdminSite'


# end of file

