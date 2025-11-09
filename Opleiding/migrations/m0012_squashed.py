# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal
import datetime


def maak_functie_mo(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='MO', beschrijving='Manager Opleidingen').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Opleiding', 'm0006_squashed'),
                ('Opleiding', 'm0007_moment'),
                ('Opleiding', 'm0008_bestelling'),
                ('Opleiding', 'm0009_afgemeld'),
                ('Opleiding', 'm0010_remove_auto_now'),
                ('Opleiding', 'm0011_timezone')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('Functie', 'm0025_squashed'),
        ('Locatie', 'm0009_squashed'),
        ('Sporter', 'm0033_squashed'),
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
        migrations.CreateModel(
            name='OpleidingMoment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField(default='2000-01-01')),
                ('begin_tijd', models.TimeField(default='10:00')),
                ('duur_minuten', models.PositiveIntegerField(default=1)),
                ('opleider_naam', models.CharField(blank=True, default='', max_length=150)),
                ('opleider_email', models.EmailField(blank=True, default='', max_length=254)),
                ('opleider_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                              to='Locatie.evenementlocatie')),
                ('aantal_dagen', models.PositiveSmallIntegerField(default=1)),
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
                ('aantal_momenten', models.PositiveIntegerField(default=1)),
                ('aantal_uren', models.PositiveSmallIntegerField(default=1)),
                ('beschrijving', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('V', 'Voorbereiden'), ('I', 'Inschrijven'),
                                                     ('G', 'Inschrijving gesloten'), ('A', 'Geannuleerd')],
                                            default='V', max_length=1)),
                ('eis_instaptoets', models.BooleanField(blank=True, default=False)),
                ('ingangseisen', models.TextField(blank=True, default='')),
                ('leeftijd_min', models.PositiveIntegerField(default=16)),
                ('leeftijd_max', models.PositiveIntegerField(default=0)),
                ('kosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('momenten', models.ManyToManyField(blank=True, to='Opleiding.opleidingmoment')),
                ('aantal_dagen', models.PositiveSmallIntegerField(default=1)),
                ('laten_zien', models.BooleanField(default=True)),
                ('periode_begin', models.DateField(default='2024-01-01')),
                ('periode_einde', models.DateField(default='2024-01-01')),
            ],
            options={
                'verbose_name': 'Opleiding',
                'verbose_name_plural': 'Opleidingen',
            },
        ),
        migrations.CreateModel(
            name='OpleidingInschrijving',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_aangemeld', models.DateTimeField(auto_now_add=True)),
                ('bedrag_ontvangen', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('aanpassing_email', models.EmailField(blank=True, max_length=254)),
                ('aanpassing_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('aanpassing_geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                            to='Account.account')),
                ('opleiding', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Opleiding.opleiding')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
                ('nummer', models.BigIntegerField(default=0)),
                ('status', models.CharField(choices=[('I', 'Inschrijven'), ('R', 'Reservering'), ('B', 'Besteld'),
                                                     ('D', 'Definitief'), ('A', 'Afgemeld')],
                                            default='I', max_length=2)),
                ('log', models.TextField(blank=True)),
                ('bestelling', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT,
                                                 to='Bestelling.bestellingregel')),
            ],
            options={
                'verbose_name': 'Opleiding inschrijving',
                'verbose_name_plural': 'Opleiding inschrijvingen',
            },
        ),
        migrations.CreateModel(
            name='OpleidingAfgemeld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_afgemeld', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('C', 'Geannuleerd'), ('A', 'Afgemeld')], max_length=2)),
                ('wanneer_aangemeld', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0,
                                                                                     tzinfo=datetime.timezone.utc))),
                ('nummer', models.BigIntegerField(default=0)),
                ('bedrag_ontvangen', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('bedrag_retour', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('aanpassing_email', models.EmailField(blank=True, max_length=254)),
                ('aanpassing_telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('aanpassing_geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('log', models.TextField(blank=True)),
                ('koper', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                            to='Account.account')),
                ('opleiding', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Opleiding.opleiding')),
                ('sporter', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporter')),
                ('bestelling', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT,
                                                 to='Bestelling.bestellingregel')),
            ],
            options={
                'verbose_name': 'Opleiding afmelding',
                'verbose_name_plural': 'Opleiding afmeldingen',
            },
        ),
        migrations.RunPython(maak_functie_mo),
    ]

# end of file
