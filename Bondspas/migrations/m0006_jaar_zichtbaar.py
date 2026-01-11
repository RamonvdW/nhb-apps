# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Bondspas', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BondspasJaar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zichtbaar', models.BooleanField(default=False)),
                ('jaar', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'ordering': ['-jaar'],
                'verbose_name': 'Bondspas jaar',
                'verbose_name_plural': 'Bondspas jaren'
            },
        ),
    ]

# end of file
