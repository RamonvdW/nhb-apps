# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0030_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='account',
            name='is_BB',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='account',
            name='is_geblokkeerd_tot',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='otp_code',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AlterField(
            model_name='account',
            name='otp_is_actief',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='account',
            name='username',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='verkeerd_wachtwoord_teller',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='account',
            name='vraag_nieuw_wachtwoord',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
