# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleidingen', 'm0008_instaptoets'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='opleiding',
            name='is_basiscursus',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='status',
            field=models.CharField(choices=[('V', 'Voorbereiden'), ('I', 'Inschrijven'), ('G', 'Inschrijving gesloten'),
                                            ('A', 'Geannuleerd')], default='V', max_length=1),
        ),
    ]

# end of file
