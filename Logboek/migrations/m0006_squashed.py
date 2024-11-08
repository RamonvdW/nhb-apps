# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='LogboekRegel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toegevoegd_op', models.DateTimeField()),
                ('gebruikte_functie', models.CharField(max_length=100)),
                ('activiteit', models.CharField(max_length=500)),
                ('actie_door_account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                                         to='Account.account')),
            ],
            options={
                'verbose_name': 'Logboek regel',
                'verbose_name_plural': 'Logboek regels',
            },
        ),
    ]

# end of file
