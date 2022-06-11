# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Competitie', 'm0073_inschrijf_voorkeur_rk_bk'),
    ]

    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='aangemeld_door',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.Account'),
        ),
    ]

# end of file
