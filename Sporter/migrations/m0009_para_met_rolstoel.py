# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0008_adres_code'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sportervoorkeuren',
            name='para_met_rolstoel',
            field=models.BooleanField(default=False),
        ),
    ]

# end of file
