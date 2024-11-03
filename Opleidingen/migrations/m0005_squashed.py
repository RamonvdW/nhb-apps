# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


def maak_functie_mo(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='MO', beschrijving='Manager Opleidingen').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Sporter', 'm0031_squashed'),
        ('Wedstrijden', 'm0057_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='OpleidingMoment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField(default='2000-01-01')),
                ('begin_tijd', models.TimeField(default='10:00')),
                ('duur_minuten', models.PositiveIntegerField(default=1)),
                ('opleider_naam', models.CharField(default='', max_length=150)),
                ('opleider_email', models.CharField(max_length=150)),
                ('opleider_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                              to='Locatie.locatie')),
            ],
            options={
                'verbose_name': 'Opleiding moment',
                'verbose_name_plural': 'Opleiding momenten',
            },
        ),
        migrations.CreateModel(
            name='OpleidingDeelnemer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_aangemeld', models.DateTimeField(auto_now=True)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('aanpassing_email', models.EmailField(blank=True, max_length=254)),
                ('aanpassing_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('aanpassing_geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                            to='Account.account')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Opleiding deelnemer',
            },
        ),
        migrations.CreateModel(
            name='Opleiding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=75)),
                ('periode_jaartal', models.PositiveSmallIntegerField(default=0)),
                ('periode_kwartaal', models.PositiveIntegerField(default=1)),
                ('aantal_momenten', models.PositiveIntegerField(default=1)),
                ('aantal_uren', models.PositiveIntegerField(default=1)),
                ('beschrijving', models.TextField(default='')),
                ('status', models.CharField(choices=[('V', ''), ('I', ''), ('A', '')], default='V', max_length=1)),
                ('ingangseisen', models.TextField()),
                ('leeftijd_min', models.PositiveIntegerField(default=16)),
                ('leeftijd_max', models.PositiveIntegerField(default=0)),
                ('kosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('deelnemers', models.ManyToManyField(blank=True, to='Opleidingen.opleidingdeelnemer')),
                ('momenten', models.ManyToManyField(blank=True, to='Opleidingen.opleidingmoment')),
            ],
            options={
                'verbose_name': 'Opleiding',
                'verbose_name_plural': 'Opleidingen',
            },
        ),
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
        migrations.RunPython(maak_functie_mo),
    ]

# end of file
