# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0003_betaalmutatie_ontvanger'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaalmutatie',
            name='url_checkout',
            field=models.CharField(default='', max_length=200),
        ),
    ]

# end of file
