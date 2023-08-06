# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='nhbvereniging',
            name='adres_regel1',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='nhbvereniging',
            name='adres_regel2',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='nhbvereniging',
            name='naam',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='nhbvereniging',
            name='plaats',
            field=models.CharField(blank=True, max_length=35),
        ),
    ]

# end of file
