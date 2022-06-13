# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0014_squashed'),
        ('Wedstrijden', 'm0020_squashed')
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Uitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField()),
                ('is_bevroren', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
            ],
            options={
                'verbose_name': 'Uitslag',
                'verbose_name_plural': 'Uitslagen',
            },
        ),
    ]

# end of file
