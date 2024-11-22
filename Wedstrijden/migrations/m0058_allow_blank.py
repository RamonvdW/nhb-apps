# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # migratie functies
    dependencies = [
        ('Wedstrijden', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijd',
            name='url_uitslag_1',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='url_uitslag_2',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='url_uitslag_3',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='url_uitslag_4',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='url_flyer',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]

# end of file
