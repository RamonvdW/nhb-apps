# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0028_scheids'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='account',
            name='is_BB',
            field=models.BooleanField(default=False, help_text='Manager MH'),
        ),
    ]

# end of file
