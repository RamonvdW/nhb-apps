# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='ExterneScores',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_actief', models.BooleanField(default=False)),
                ('type', models.PositiveSmallIntegerField(choices=[(0, 'Onbekend'), (1, 'Centaur')], default=0)),
                ('url_auth', models.CharField(blank=True, default='', max_length=128)),
                ('url_ophalen', models.CharField(blank=True, default='', max_length=128)),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging')),
                ('password', models.CharField(blank=True, default='', max_length=128)),
                ('username', models.CharField(blank=True, default='', max_length=128)),
            ],
            options={
                'verbose_name': 'Externe scores',
                'verbose_name_plural': 'Externe scores',
            },
        ),
    ]

# end of file
