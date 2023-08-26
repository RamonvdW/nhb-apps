# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0103_vereniging_2'),
        ('Vereniging', 'm0003_vereniging_2'),
        ('Functie', 'm0022_scheidsrechters'),
        ('NhbStructuur', 'm0035_delete_nhbvereniging'),
    ]

    # migratie functies
    operations = [
        migrations.RenameModel(
            old_name='NhbCluster',
            new_name='Cluster',
        ),
        migrations.RenameModel(
            old_name='NhbRayon',
            new_name='Rayon',
        ),
        migrations.RenameModel(
            old_name='NhbRegio',
            new_name='Regio',
        ),
        migrations.AlterModelOptions(
            name='cluster',
            options={'verbose_name': 'Cluster'},
        ),
        migrations.AlterModelOptions(
            name='rayon',
            options={'verbose_name': 'Rayon'},
        ),
        migrations.AlterModelOptions(
            name='regio',
            options={'verbose_name': 'Regio', 'verbose_name_plural': "Regio's"},
        ),
    ]

# end of file
