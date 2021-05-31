# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0002_updates'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='begrenzing',
            field=models.CharField(choices=[('L', 'Landelijk'), ('Y', 'Rayon'), ('G', 'Regio'), ('V', 'Vereniging')], default='L', max_length=1),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijd',
            name='bijzonderheden',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
    ]

# end of file
