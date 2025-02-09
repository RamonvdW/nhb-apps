# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0004_opleiding_2'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BestellingRegel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('korte_beschrijving', models.CharField(blank=True, default='?', max_length=250)),
                ('btw_percentage', models.CharField(blank=True, default='', max_length=5)),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('korting_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('btw_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
                ('code', models.CharField(blank=True, default='?', max_length=10)),
            ],
            options={
                'verbose_name': 'Bestelling regel',
            },
        ),
        migrations.AddField(
            model_name='bestelling',
            name='regels',
            field=models.ManyToManyField(to='Bestelling.bestellingregel'),
        ),
        migrations.AddField(
            model_name='bestellingmandje',
            name='regels',
            field=models.ManyToManyField(to='Bestelling.bestellingregel'),
        ),
    ]

# end of file
