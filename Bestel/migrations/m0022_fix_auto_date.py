# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0021_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='bestelling',
            name='aangemaakt',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

# end of file
