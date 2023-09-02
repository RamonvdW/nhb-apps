# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Geo', 'm0001_initial_copy'),
        ('Vereniging', 'm0004_geo_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='vereniging',
            name='clusters',
        ),
        migrations.RenameField(
            model_name='vereniging',
            old_name='geo_clusters',
            new_name='clusters',
        ),
        migrations.AlterField(
            model_name='vereniging',
            name='clusters',
            field=models.ManyToManyField(blank=True, to='Geo.cluster'),
        ),

        migrations.RemoveField(
            model_name='vereniging',
            name='regio',
        ),
        migrations.RenameField(
            model_name='vereniging',
            old_name='geo_regio',
            new_name='regio',
        ),
        migrations.AlterField(
            model_name='vereniging',
            name='regio',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.regio'),
        ),
    ]

# end of file
