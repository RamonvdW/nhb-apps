# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Betalingen.models import BETALINGEN_HOOGSTE_PK


def init_hoogste_boekingsnummer(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hoogste_klas = apps.get_model('Betalingen', 'BetalingenHoogsteBoekingsnummer')

    # maak het enige record aan met het startnummer voor de boekingsnummers
    hoogste_klas(
            pk=BETALINGEN_HOOGSTE_PK,
            hoogste_gebruikte_boekingsnummer=1000000).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0024_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BetalingenActieveTransacties',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('payment_id', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name': 'Betalingen actieve transacties',
            },
        ),
        migrations.CreateModel(
            name='BetalingenMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('boekingsnummer', models.PositiveIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('payment_id', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name': 'Betalingen mutatie',
            },
        ),
        migrations.CreateModel(
            name='BetalingenVerenigingInstellingen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mollie_api_key', models.CharField(max_length=50)),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Betalingen vereniging instellingen',
            },
        ),
        migrations.CreateModel(
            name='BetalingenHoogsteBoekingsnummer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_gebruikte_boekingsnummer', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.RunPython(init_hoogste_boekingsnummer),
    ]

# end of file
