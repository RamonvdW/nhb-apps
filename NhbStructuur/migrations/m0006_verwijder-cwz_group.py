# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0005_vereniging_cwz_group'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='nhbvereniging',
            name='cwz_group',
        ),
    ]

# end of file
