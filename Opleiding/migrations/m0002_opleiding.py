# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
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

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Locatie', 'm0009_squashed'),
        ('Opleiding', 'm0001_diploma'),
        ('Opleidingen', 'm0011_remove'),
        ('Sporter', 'm0031_squashed'),
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
                ('opleider_email', models.EmailField(blank=True, default='', max_length=254)),
                ('opleider_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                              to='Locatie.evenementlocatie')),
            ],
            options={
                'verbose_name': 'Opleiding moment',
                'verbose_name_plural': 'Opleiding momenten',
            },
        ),
        migrations.CreateModel(
            name='Opleiding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=75)),
                ('is_basiscursus', models.BooleanField(default=False)),
                ('periode_jaartal', models.PositiveSmallIntegerField(default=0)),
                ('periode_kwartaal', models.PositiveIntegerField(default=1)),
                ('aantal_momenten', models.PositiveIntegerField(default=1)),
                ('aantal_uren', models.PositiveIntegerField(default=1)),
                ('beschrijving', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('V', 'Voorbereiden'), ('I', 'Inschrijven'), ('G', 'Inschrijving gesloten'), ('A', 'Geannuleerd')], default='V', max_length=1)),
                ('eis_instaptoets', models.BooleanField(blank=True, default=False)),
                ('ingangseisen', models.TextField(blank=True, default='')),
                ('leeftijd_min', models.PositiveIntegerField(default=16)),
                ('leeftijd_max', models.PositiveIntegerField(default=0)),
                ('kosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('momenten', models.ManyToManyField(blank=True, to='Opleiding.opleidingmoment')),
            ],
            options={
                'verbose_name': 'Opleiding',
                'verbose_name_plural': 'Opleidingen',
            },
        ),
        migrations.CreateModel(
            name='OpleidingDeelnemer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_aangemeld', models.DateTimeField(auto_now_add=True)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('retour_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('aanpassing_email', models.EmailField(blank=True, max_length=254)),
                ('aanpassing_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('aanpassing_geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                            to='Account.account')),
                ('opleiding', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Opleiding.opleiding')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Opleiding deelnemer',
            },
        ),
        # TODO: aanzetten bij opruimen app Opleidingen
        # migrations.RunPython(maak_functie_mo),
    ]

# end of file
