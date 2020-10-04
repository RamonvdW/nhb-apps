# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0002_add_is_ag'),
        ('Wedstrijden', 'm0003_admin_blank_fields'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdUitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
            ],
            options={
                'verbose_name': 'Wedstrijduitslag',
                'verbose_name_plural': 'Wedstrijduitslagen',
            },
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='uitslag',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdUitslag'),
        ),
    ]

# end of file
