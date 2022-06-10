# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0072_limiet_split'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='inschrijf_voorkeur_rk_bk',
            field=models.BooleanField(default=True),
        ),
    ]

# end of file
