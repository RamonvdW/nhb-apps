# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Feedback', 'm0001_migrate'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='feedback',
            name='in_rol',
            field=models.CharField(blank=True, default='?', max_length=100),
        ),
    ]

# end of file
