# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0030_bondsbureau'),
        ('Competitie', 'm0083_kampioenschap_4'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='regiocompetitieteam',
            name='vereniging',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging'),
        ),
    ]

# end of file