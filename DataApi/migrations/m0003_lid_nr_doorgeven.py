# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # afhankelijkheden
    dependencies = [
        ('DataApi', 'm0002_allow_blank'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='dataapilidmaatschap',
            name='lid_nr_doorgeven',
            field=models.BooleanField(default=True),
        ),
    ]

# end of file
