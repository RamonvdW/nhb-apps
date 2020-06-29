# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0012_migrate_cwz_hwl'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='nhbvereniging',
            name='clusters',
            field=models.ManyToManyField(blank=True, to='NhbStructuur.NhbCluster'),
        ),
    ]

# end of file
