# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0011_ver_plaats_regio'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='boogtype',
            field=models.CharField(max_length=5),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='indiv_klasse',
            field=models.CharField(max_length=35),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='vereniging_plaats',
            field=models.CharField(max_length=35),
        ),
    ]

# end of file
