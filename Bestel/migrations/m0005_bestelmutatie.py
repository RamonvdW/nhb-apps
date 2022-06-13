# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Bestel', 'm0004_bestelling_status'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BestelMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelproduct')),
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
                ('kortingscode', models.CharField(blank=True, default='', max_length=20)),
            ],
            options={
                'verbose_name': 'Bestel mutatie',
            },
        ),
        migrations.AlterField(
            model_name='bestelling',
            name='status',
            field=models.CharField(choices=[('N', 'N'), ('B', 'B'), ('A', 'A')], default='N', max_length=1),
        ),
    ]

# end of file
