# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0006_squashed1'),
        ('Sporter', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Secretaris',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sporters', models.ManyToManyField(blank=True, to='Sporter.sporter')),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Secretaris Vereniging',
                'verbose_name_plural': 'Secretaris Vereniging',
            },
        ),
    ]

# end of file
