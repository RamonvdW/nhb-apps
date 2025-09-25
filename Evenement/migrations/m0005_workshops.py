# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models, migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0004_afgemeld'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='evenement',
            name='workshop_keuze',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='evenementinschrijving',
            name='gekozen_workshops',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]

# end of file
