# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        #migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Account', 'm0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogboekRegel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField()),
                ('gebruikte_functie', models.CharField(max_length=100)),
                ('activiteit', models.CharField(max_length=500)),
                ('actie_door_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Account.Account', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Logboek regel',
                'verbose_name_plural': 'Logboek regels',
            },
        ),
    ]
