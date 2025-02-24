# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Scheidsrechter', 'm0012_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='scheidsmutatie',
            name='door',
            field=models.CharField(default='', max_length=150),
        ),
    ]

# end of file
