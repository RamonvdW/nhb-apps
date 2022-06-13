# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
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
            hoogste_gebruikte_bestel_nr=1000000).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Betaal', 'm0001_initial'),
        ('Kalender', 'm0008_inschrijving'),
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
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
            ],
            options={
                'verbose_name': 'Bestel product',
                'verbose_name_plural': 'Bestel producten',
            },
        ),
        migrations.CreateModel(
            name='BestelMandje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('totaal_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=7)),
                ('account', models.OneToOneField(on_delete=models.deletion.CASCADE, to='Account.account')),
                ('producten', models.ManyToManyField(to='Bestel.BestelProduct')),
            ],
            options={
                'verbose_name': 'Mandje',
                'verbose_name_plural': 'Mandjes',
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
                ('producten', models.ManyToManyField(to='Bestel.BestelProduct')),
                ('transacties', models.ManyToManyField(to='Betaal.BetaalTransactie')),
            ],
            options={
                'verbose_name': 'Bestelling',
                'verbose_name_plural': 'Bestellingen',
            },
        ),
        migrations.RunPython(init_hoogste_bestel_nr),
    ]

# end of file
