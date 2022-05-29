# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0006_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='sportervoorkeuren',
            name='opmerking_para_sporter',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]

# end of file