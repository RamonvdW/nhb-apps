# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='histcompetitieindividueel',
            name='boogtype',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]

# end of file
