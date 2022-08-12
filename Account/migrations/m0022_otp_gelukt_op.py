# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0021_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='account',
            name='otp_controle_gelukt_op',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

# end of file
