# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Records', 'm0014_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='anderrecord',
            name='volgorde',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='anderrecord',
            name='datum',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AlterModelOptions(
            name='anderrecord',
            options={'verbose_name': 'Ander record', 'verbose_name_plural': 'Andere records'},
        ),
    ]

# end of file
