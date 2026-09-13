# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # afhankelijkheden
    dependencies = [
        ('DataApi', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='dataapilidmaatschap',
            name='afmeld_datum',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='dataapivereniging',
            name='afmeld_datum',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]

# end of file
