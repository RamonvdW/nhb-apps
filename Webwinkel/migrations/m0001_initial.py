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
    dependencies = []

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
                ('bestel_begrenzing', models.CharField(blank=True, default='1', help_text='1-10,20,25,30,50', max_length=100)),
                ('fotos', models.ManyToManyField(blank=True, to='Webwinkel.WebwinkelFoto')),
                ('omslag_foto', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='omslagfoto', to='Webwinkel.webwinkelfoto')),
            ],
            options={
                'verbose_name': 'Webwinkel product',
                'verbose_name_plural': 'Webwinkel producten',
            },
        ),
    ]

# end of file
