# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Spelden', 'm0001_initial'),
                ('Spelden', 'm0002_spelden'),
                ('Spelden', 'm0003_speldscore'),
                ('Spelden', 'm0004_defaults'),
                ('Spelden', 'm0005_defaults')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0062_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Wedstrijden', 'm0063_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SpeldAanvraag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt_op', models.DateField(auto_now_add=True)),
                ('last_email_reminder', models.DateTimeField(auto_now_add=True)),
                ('soort_speld', models.CharField(choices=[('Ws', 'WA ster'),
                                                          ('Wsz', 'WA zilveren ster'),
                                                          ('Wt', 'WA target award'),
                                                          ('Wtz', 'WA zilveren target award'),
                                                          ('Wa', 'WA arrowhead speld'),
                                                          ('Ngi', 'NL graadspeld indoor'),
                                                          ('Ngo', 'NL graadspeld outdoor'),
                                                          ('Ngv', 'NL graadspeld veld'),
                                                          ('Ngs', 'NL graadspeld short metric'),
                                                          ('Nga', 'NL graadspeld algemeen'),
                                                          ('Nt', 'NL tussenspeld')],
                                                 default='Ws', max_length=3)),
                ('datum_wedstrijd', models.DateField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'),
                                                         ('IN', 'Indoor'),
                                                         ('VE', 'Veld')],
                                                default='OD', max_length=2)),
                ('log', models.TextField(blank=True, default='')),
                ('boog_type', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('door_account', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('leeftijdsklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.leeftijdsklasse')),
                ('voor_sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='Wedstrijden.wedstrijd')),
            ],
            options={
                'verbose_name': 'Speld aanvraag',
                'verbose_name_plural': 'Speld aanvragen',
            },
        ),
        migrations.CreateModel(
            name='SpeldBijlage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('soort_bijlage', models.CharField(choices=[('s', 'Scorebriefje'),
                                                            ('u', 'Uitslag')],
                                                   default='s', max_length=1)),
                ('bestandstype', models.CharField(choices=[('f', 'Foto'),
                                                           ('p', 'PDF'),
                                                           ('?', '?')],
                                                  default='f', max_length=1)),
                ('log', models.TextField(blank=True, default='')),
                ('aanvraag', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Spelden.speldaanvraag')),
            ],
            options={
                'verbose_name': 'Speld bijlage',
                'verbose_name_plural': 'Speld bijlagen',
            },
        ),
        migrations.CreateModel(
            name='Speld',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=30)),
                ('categorie', models.CharField(choices=[('Ws', 'WA ster'),
                                                        ('Wsz', 'WA zilveren ster'),
                                                        ('Wt', 'WA target award'),
                                                        ('Wtz', 'WA zilveren target award'),
                                                        ('Wa', 'WA arrowhead speld'),
                                                        ('Ngi', 'NL graadspeld indoor'),
                                                        ('Ngo', 'NL graadspeld outdoor'),
                                                        ('Ngv', 'NL graadspeld veld'),
                                                        ('Ngs', 'NL graadspeld short metric'),
                                                        ('Nga', 'NL graadspeld algemeen'),
                                                        ('Nt', 'NL tussenspeld')],
                                               max_length=3)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='BasisTypen.boogtype')),
                ('prijs_euro', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6)),
            ],
            options={
                'verbose_name': 'Speld',
                'verbose_name_plural': 'Spelden',
            },
        ),
        migrations.CreateModel(
            name='SpeldScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wedstrijd_soort', models.CharField(max_length=20)),
                ('speld', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Spelden.speld')),
                ('benodigde_score', models.PositiveSmallIntegerField()),
                ('afstand', models.PositiveSmallIntegerField(default=0)),
                ('aantal_doelen', models.PositiveSmallIntegerField(default=0)),
                ('boog_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                to='BasisTypen.boogtype')),
                ('leeftijdsklasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.leeftijdsklasse')),
            ],
            options={
                'verbose_name': 'Speld score',
                'verbose_name_plural': 'Speld scores',
            },
        ),
    ]

# end of file
