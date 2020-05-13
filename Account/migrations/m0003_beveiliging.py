# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0002_schutterboog'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='account',
            name='is_geblokkeerd_tot',
            field=models.DateTimeField(blank=True, help_text='Login niet mogelijk tot', null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='verkeerd_wachtwoord_teller',
            field=models.IntegerField(default=0, help_text='Aantal mislukte inlog pogingen op rij'),
        ),
    ]

# end of file
