# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0017_langere_url'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaalmutatie',
            name='pogingen',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='betaalmutatie',
            name='beschrijving',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='betaalmutatie',
            name='url_betaling_gedaan',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]

# end of file
