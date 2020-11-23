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
        ('Competitie', 'm0019_rank'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='KampioenschapMutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('deelnemer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.KampioenschapSchutterBoog')),
            ],
            options={
                'verbose_name': 'Kampioenschap Mutatie',
                'verbose_name_plural': 'Kampioenschap Mutaties',
            },
        ),
        migrations.AddField(
            model_name='competitietaken',
            name='hoogste_mutatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Competitie.KampioenschapMutatie'),
        ),
    ]

# end of file
