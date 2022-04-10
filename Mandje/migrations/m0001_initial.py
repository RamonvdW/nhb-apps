# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0019_squashed'),
        ('Kalender', 'm0010_inschrijving'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='MandjeTransactie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer', models.DateTimeField()),
                ('euros', models.DecimalField(decimal_places=2, max_digits=7)),
                ('zender', models.CharField(max_length=200)),
                ('ontvanger', models.CharField(max_length=200)),
            ],
            options={'verbose_name': 'Mandje transactie'},
        ),
        migrations.CreateModel(
            name='MandjeInhoud',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Account.account')),
                ('inschrijving', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Kalender.kalenderinschrijving')),
            ],
            options={'verbose_name': 'Mandje inhoud', 'verbose_name_plural': 'Mandje inhoud'},
        ),
    ]

# end of file
