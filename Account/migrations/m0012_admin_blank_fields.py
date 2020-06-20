# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0011_migratie_functie_nhblid_part3'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='account',
            name='otp_code',
            field=models.CharField(blank=True, default='', help_text='OTP code', max_length=16),
        ),
    ]

# end of file
