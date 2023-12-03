# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0029_adres'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='scheids_opt_in_korps_email',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='scheids_opt_in_korps_tel_nr',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='scheids_opt_in_ver_email',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='scheids_opt_in_ver_tel_nr',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='sporter',
            name='adres_lat',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='sporter',
            name='adres_lon',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]

# end of file
