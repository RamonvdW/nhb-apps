# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0107_geo_2'),
        ('Functie', 'm0024_geo_2'),
        ('NhbStructuur', 'm0037_rayon_nr'),
        ('Vereniging', 'm0005_geo_2'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='Cluster',
        ),
        migrations.DeleteModel(
            name='Regio',
        ),
        migrations.DeleteModel(
            name='Rayon',
        ),
    ]

# end of file
