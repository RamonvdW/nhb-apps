# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleidingen', 'm0007_locatie'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='opleiding',
            name='eis_instaptoets',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='eis_instaptoets',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='ingangseisen',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='beschrijving',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='status',
            field=models.CharField(choices=[('V', 'Voorbereiden'), ('I', 'Inschrijven'), ('A', 'Geannuleerd')],
                                   default='V', max_length=1),
        ),
    ]

# end of file
