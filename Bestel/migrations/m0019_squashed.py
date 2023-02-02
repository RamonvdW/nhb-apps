# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Bestel.models import BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK
from decimal import Decimal


def init_hoogste_bestel_nr(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hoogste_klas = apps.get_model('Bestel', 'BestelHoogsteBestelNr')

    # maak het enige record aan met het hoogste gebruikte bestelnummer
    hoogste_klas(
            pk=BESTEL_HOOGSTE_BESTEL_NR_FIXED_PK,
            hoogste_gebruikte_bestel_nr=1002000).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Bestel', 'm0015_squashed'),
                ('Bestel', 'm0016_webwinkel'),
                ('Bestel', 'm0017_kosten'),
                ('Bestel', 'm0018_annuleer')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('Betaal', 'm0011_squashed'),
        ('Webwinkel', 'm0002_keuze'),
        ('Wedstrijden', 'm0031_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BestelHoogsteBestelNr',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_gebruikte_bestel_nr', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='BestelProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('wedstrijd_inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdinschrijving')),
                ('webwinkel_keuze', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Webwinkel.webwinkelkeuze')),
            ],
            options={
                'verbose_name': 'Bestel product',
                'verbose_name_plural': 'Bestel producten',
            },
        ),
        migrations.CreateModel(
            name='Bestelling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bestel_nr', models.PositiveIntegerField()),
                ('aangemaakt', models.DateTimeField(auto_now=True)),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('log', models.TextField()),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Account.account')),
                ('producten', models.ManyToManyField(to='Bestel.bestelproduct')),
                ('transacties', models.ManyToManyField(blank=True, to='Betaal.betaaltransactie')),
                ('betaal_mutatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalmutatie')),
                ('betaal_actief', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Betaal.betaalactief')),
                ('ontvanger', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Betaal.betaalinstellingenvereniging')),
                ('status', models.CharField(choices=[('N', 'Nieuw'), ('B', 'Te betalen'), ('A', 'Afgerond'), ('F', 'Mislukt'), ('G', 'Geannuleerd')], default='N', max_length=1)),
                ('verkoper_adres1', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_adres2', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_email', models.EmailField(blank=True, default='', max_length=254)),
                ('verkoper_kvk', models.CharField(blank=True, default='', max_length=15)),
                ('verkoper_naam', models.CharField(blank=True, default='', max_length=100)),
                ('verkoper_telefoon', models.CharField(blank=True, default='', max_length=20)),
                ('verkoper_bic', models.CharField(blank=True, default='', max_length=11)),
                ('verkoper_heeft_mollie', models.BooleanField(default=False)),
                ('verkoper_iban', models.CharField(blank=True, default='', max_length=18)),
                ('btw_euro_cat1', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat2', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat3', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_percentage_cat1', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat2', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat3', models.CharField(blank=True, default='', max_length=5)),
                ('verzendkosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
            ],
            options={
                'verbose_name': 'Bestelling',
                'verbose_name_plural': 'Bestellingen',
            },
        ),
        migrations.CreateModel(
            name='BestelMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelproduct')),
                ('korting', models.CharField(blank=True, default='', max_length=20)),
                ('bestelling', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Bestel.bestelling')),
                ('betaling_is_gelukt', models.BooleanField(default=False)),
                ('wedstrijd_inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdinschrijving')),
                ('bedrag_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('webwinkel_keuze', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Webwinkel.webwinkelkeuze')),
            ],
            options={
                'verbose_name': 'Bestel mutatie',
            },
        ),
        migrations.CreateModel(
            name='BestelMandje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('account', models.OneToOneField(on_delete=models.deletion.CASCADE, to='Account.account')),
                ('producten', models.ManyToManyField(to='Bestel.bestelproduct')),
                ('btw_euro_cat1', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat2', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_euro_cat3', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('btw_percentage_cat1', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat2', models.CharField(blank=True, default='', max_length=5)),
                ('btw_percentage_cat3', models.CharField(blank=True, default='', max_length=5)),
                ('verzendkosten_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
            ],
            options={
                'verbose_name': 'Mandje',
                'verbose_name_plural': 'Mandjes',
            },
        ),
        migrations.RunPython(init_hoogste_bestel_nr),
    ]

# end of file
