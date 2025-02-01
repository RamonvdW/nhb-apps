# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleiding', 'm0003_log'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='opleiding',
            name='periode_jaartal',
        ),
        migrations.RemoveField(
            model_name='opleiding',
            name='periode_kwartaal',
        ),
        migrations.AddField(
            model_name='opleiding',
            name='aantal_dagen',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='opleiding',
            name='laten_zien',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='opleiding',
            name='periode_begin',
            field=models.DateField(default='2024-01-01'),
        ),
        migrations.AddField(
            model_name='opleiding',
            name='periode_einde',
            field=models.DateField(default='2024-01-01'),
        ),
        migrations.AlterField(
            model_name='opleiding',
            name='aantal_uren',
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]

# end of file
