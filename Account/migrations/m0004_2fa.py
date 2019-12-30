# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    dependencies = [
        ('Account', 'm0003_beveiliging'),
    ]

    operations = [
        # verwijder velden die niet meer nodig zijn
        migrations.RemoveField(
            model_name='account',
            name='extra_info_pogingen',
        ),
        migrations.RemoveField(
            model_name='account',
            name='is_voltooid',
        ),

        # voeg velden toe voor OTP
        migrations.AddField(
            model_name='account',
            name='otp_code',
            field=models.CharField(default='', help_text='OTP code', max_length=16),
        ),
        migrations.AddField(
            model_name='account',
            name='otp_is_actief',
            field=models.BooleanField(default=False, help_text='Is OTP verificatie gelukt'),
        ),
    ]

# end of file
