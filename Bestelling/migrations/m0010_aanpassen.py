# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0059_squashed'),
        ('Bestelling', 'm0009_remove_verzendkosten'),
        ('Sporter', 'm0031_squashed'),
        ('Wedstrijden', 'm0060_bestelling'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestellingmutatie',
            name='sessie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Wedstrijden.wedstrijdsessie'),
        ),
        migrations.AddField(
            model_name='bestellingmutatie',
            name='sporterboog',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Sporter.sporterboog'),
        ),
        migrations.AddField(
            model_name='bestellingmutatie',
            name='wedstrijdklasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='BasisTypen.kalenderwedstrijdklasse'),
        ),
    ]


# end of file
