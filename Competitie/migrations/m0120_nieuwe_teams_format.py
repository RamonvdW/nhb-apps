# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0119_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='result_bk_teamscore_1',
        ),
        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='result_bk_teamscore_2',
        ),
        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='result_rk_teamscore_1',
        ),
        migrations.RemoveField(
            model_name='kampioenschapsporterboog',
            name='result_rk_teamscore_2',
        ),
        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='result_counts',
        ),
        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='rk_kampioen_label',
        ),
    ]

# end of file
