# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


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
            name='BetaalActief',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('payment_id', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': 'Actief payment_id',
                'verbose_name_plural': "Actieve payment_id's",
            },
        ),
        migrations.CreateModel(
            name='BetaalMutatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('code', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=100)),
                ('bedrag_euro', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('payment_id', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': 'Betaal mutatie',
            },
        ),
        migrations.CreateModel(
            name='BetaalTransactie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.CharField(max_length=64)),
                ('when', models.DateTimeField()),
                ('beschrijving', models.CharField(max_length=100)),
                ('is_restitutie', models.BooleanField(default=False)),
                ('bedrag_euro', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('klant_naam', models.CharField(max_length=100)),
                ('klant_iban', models.CharField(max_length=18)),
                ('klant_bic', models.CharField(max_length=11)),
            ],
        ),
        migrations.CreateModel(
            name='BetaalInstellingenVereniging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mollie_api_key', models.CharField(max_length=50)),
                ('akkoord_via_nhb', models.BooleanField(default=False)),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Betaal instellingen vereniging',
                'verbose_name_plural': 'Betaal instellingen verenigingen',
            },
        ),
    ]

# end of file
