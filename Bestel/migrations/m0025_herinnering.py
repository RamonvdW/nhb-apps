# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0024_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelmandje',
            name='vorige_herinnering',
            field=models.DateField(default='2000-01-01'),
        ),
    ]

# end of file
