# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0016_verwijder_secretaris'),
        ('Opleidingen', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='OpleidingDiploma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='', max_length=5)),
                ('beschrijving', models.CharField(default='', max_length=50)),
                ('toon_op_pas', models.BooleanField(default=False)),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('datum_begin', models.DateField(default='1990-01-01')),
                ('datum_einde', models.DateField(default='9999-12-31')),
            ],
            options={
                'verbose_name': 'Opleiding diploma',
            },
        ),
    ]

# end of file
