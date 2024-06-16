# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BetaalInstellingenVereniging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mollie_api_key', models.CharField(blank=True, max_length=50)),
                ('akkoord_via_bond', models.BooleanField(default=False)),
                ('vereniging', models.OneToOneField(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Betaal instellingen vereniging',
                'verbose_name_plural': 'Betaal instellingen verenigingen',
            },
        ),
        migrations.CreateModel(
            name='BetaalActief',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('payment_id', models.CharField(max_length=64)),
                ('ontvanger', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                to='Betaal.betaalinstellingenvereniging')),
                ('log', models.TextField(default='')),
                ('payment_status', models.CharField(default='', max_length=15)),
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
                ('payment_id', models.CharField(blank=True, max_length=64)),
                ('ontvanger', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='Betaal.betaalinstellingenvereniging')),
                ('url_betaling_gedaan', models.CharField(default='', max_length=100)),
                ('url_checkout', models.CharField(blank=True, default='', max_length=200)),
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
                ('bedrag_euro_boeking', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('klant_naam', models.CharField(max_length=100)),
                ('klant_account', models.CharField(max_length=100)),
                ('bedrag_euro_klant', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('is_handmatig', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Betaal transactie',
                'verbose_name_plural': 'Betaal transacties',
            },
        ),
    ]

# end of file
