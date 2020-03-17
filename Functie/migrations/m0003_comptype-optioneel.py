# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0002_functies-2019'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='functie',
            name='comp_type',
            field=models.CharField(blank=True, default='', max_length=2),
        ),
    ]

# end of file
