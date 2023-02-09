# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Records', 'm0011_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='besteindivrecords',
            name='materiaalklasse',
            field=models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'), ('LB', 'Longbow'), ('TR', 'Traditional'), ('IB', 'Instinctive bow')], max_length=2),
        ),
        migrations.AlterField(
            model_name='indivrecord',
            name='materiaalklasse',
            field=models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'), ('LB', 'Longbow'), ('TR', 'Traditional'), ('IB', 'Instinctive bow')], max_length=2),
        ),
    ]

# end of file
