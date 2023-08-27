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
        ('Competitie', 'm0106_geo_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kampioenschap',
            name='rayon',
        ),
        migrations.RenameField(
            model_name='kampioenschap',
            old_name='geo_rayon',
            new_name='rayon',
        ),
        migrations.AlterField(
            model_name='kampioenschap',
            name='rayon',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.rayon'),
        ),

        migrations.RemoveField(
            model_name='regiocompetitie',
            name='regio',
        ),
        migrations.RenameField(
            model_name='regiocompetitie',
            old_name='geo_regio',
            new_name='regio',
        ),
        migrations.AlterField(
            model_name='regiocompetitie',
            name='regio',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.regio'),
        ),

        migrations.RemoveField(
            model_name='regiocompetitieronde',
            name='cluster',
        ),
        migrations.RenameField(
            model_name='regiocompetitieronde',
            old_name='geo_cluster',
            new_name='cluster',
        ),
        migrations.AlterField(
            model_name='regiocompetitieronde',
            name='cluster',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.cluster'),
        ),
    ]

# end of file
