# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0014_account_first_name'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='account',
            name='otp_code',
            field=models.CharField(blank=True, default='', help_text='OTP code', max_length=32),
        ),
    ]

# end of file
