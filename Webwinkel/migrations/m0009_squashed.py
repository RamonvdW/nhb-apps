# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Webwinkel.definities import WEBWINKEL_VERKOPENDE_VER_NR
from decimal import Decimal


def maak_functie_mww(apps, _):

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')
    ver_klas = apps.get_model('Vereniging', 'Vereniging')

    # MWW is gekoppeld aan vereniging 1368 omdat dat de verkopende vereniging is waar de betalingen op binnen komen
    ver = ver_klas.objects.get(ver_nr=WEBWINKEL_VERKOPENDE_VER_NR)
    functie_klas(rol='MWW', beschrijving='Manager Webwinkel', vereniging=ver).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Webwinkel', 'm0005_squashed'),
                ('Webwinkel', 'm0006_subtitel'),
                ('Webwinkel', 'm0007_kleding_maat'),
                ('Webwinkel', 'm0008_gewicht')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0025_squashed'),
        ('Vereniging', 'm0007_squashed'),
        ('Account', 'm0032_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WebwinkelFoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('locatie', models.CharField(blank=True, max_length=100)),
                ('locatie_thumb', models.CharField(blank=True, max_length=100)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Webwinkel foto',
                'verbose_name_plural': "Webwinkel foto's",
                'ordering': ('locatie', 'volgorde'),
            },
        ),
        migrations.CreateModel(
            name='WebwinkelProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mag_tonen', models.BooleanField(default=True)),
                ('volgorde', models.PositiveSmallIntegerField(default=9999)),
                ('sectie', models.CharField(blank=True, default='', max_length=50)),
                ('omslag_titel', models.CharField(blank=True, default='', max_length=25)),
                ('beschrijving', models.TextField(blank=True, default='')),
                ('bevat_aantal', models.PositiveSmallIntegerField(default=1)),
                ('eenheid', models.CharField(blank=True, default='', max_length=50)),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('onbeperkte_voorraad', models.BooleanField(default=False)),
                ('aantal_op_voorraad', models.PositiveSmallIntegerField(default=0)),
                ('bestel_begrenzing', models.CharField(blank=True, default='1', help_text='1-10,20,25,30,50',
                                                       max_length=100)),
                ('fotos', models.ManyToManyField(blank=True, to='Webwinkel.webwinkelfoto')),
                ('omslag_foto', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                                  related_name='omslagfoto', to='Webwinkel.webwinkelfoto')),
                ('type_verzendkosten', models.CharField(choices=[('pak', 'Pakketpost'), ('brief', 'Briefpost')],
                                                        default='pak', max_length=5)),
                ('sectie_subtitel', models.CharField(blank=True, default='', max_length=250)),
                ('kleding_maat', models.CharField(blank=True, default='', max_length=10)),
                ('gewicht_gram', models.SmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Webwinkel product',
                'verbose_name_plural': 'Webwinkel producten',
            },
        ),
        migrations.CreateModel(
            name='WebwinkelKeuze',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('status', models.CharField(choices=[('M', 'Reservering'), ('B', 'Besteld'), ('BO', 'Betaald'),
                                                     ('A', 'Geannuleerd')], default='M', max_length=2)),
                ('aantal', models.PositiveSmallIntegerField(default=1)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('ontvangen_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('log', models.TextField(blank=True)),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('product', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Webwinkel.webwinkelproduct')),
            ],
        ),
        migrations.RunPython(maak_functie_mww, reverse_code=migrations.RunPython.noop),
    ]

# end of file
