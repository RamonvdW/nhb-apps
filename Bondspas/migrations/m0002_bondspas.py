# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bondspas', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='bondspas',
            name='aanwezig_sinds',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bondspas',
            name='filename',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='bondspas',
            name='log',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='bondspas',
            name='opnieuw_proberen_na',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

# end of file
