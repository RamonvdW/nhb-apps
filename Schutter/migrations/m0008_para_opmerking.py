# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0007_remove_account'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='schuttervoorkeuren',
            name='opmerking_para_sporter',
            field=models.CharField(default='', max_length=256),
        ),
    ]

# end of file
