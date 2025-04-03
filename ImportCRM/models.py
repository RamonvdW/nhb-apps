# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models

# er is maar 1 (echt) record
IMPORT_LIMIETEN_PK = 42


class ImportLimieten(models.Model):

    # limieten toepassen?
    # hiermee kan het ook tijdelijk uitgezet worden
    use_limits = models.BooleanField(default=True)

    # maximum aantal wijzigingen waarbij een import gestopt moet worden.   
    max_club_changes = models.PositiveSmallIntegerField(default=50)
    max_member_changes = models.PositiveSmallIntegerField(default=250)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Import limieten"



# end of file
