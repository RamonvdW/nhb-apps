# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


def migrate_diplomas(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    old_klas = apps.get_model('Opleidingen', 'OpleidingDiploma')
    new_klas = apps.get_model('Opleiding', 'OpleidingDiploma')

    bulk = list()
    for obj in old_klas.objects.all():
        bulk.append(
            new_klas(
                sporter=obj.sporter,
                code=obj.code,
                beschrijving=obj.beschrijving,
                toon_op_pas=obj.toon_op_pas,
                datum_begin=obj.datum_begin,
                datum_einde=obj.datum_einde))

        if len(bulk) >= 500:
            new_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):
        new_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0031_squashed'),
        ('Opleidingen', 'm0010_prep_migrate'),
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
                ('datum_begin', models.DateField(default='1990-01-01')),
                ('datum_einde', models.DateField(default='9999-12-31')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Opleiding diploma',
            },
        ),
        migrations.RunPython(migrate_diplomas),
    ]

# end of file
