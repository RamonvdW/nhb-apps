# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.db.models.deletion import PROTECT, CASCADE


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0058_scheids_rk_bk'),
        ('Sporter', 'm0031_squashed'),
        ('Wedstrijden', 'm0053_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SpeldAanvraag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aangemaakt_op', models.DateField(auto_now_add=True)),
                ('last_email_reminder', models.DateTimeField(default='2000-01-01')),
                ('soort_speld', models.CharField(choices=[('Ws', 'WA ster'), ('Wt', 'WA Target award'),
                                                          ('Wa', 'WA arrowhead'), ('Ng', 'NL graadspeld'),
                                                          ('Na', 'NL graadspeld algemeen'), ('Nt', 'NL tussenspeld')],
                                                 default='Ws', max_length=2)),
                ('datum_wedstrijd', models.DateField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('IN', 'Indoor'), ('VE', 'Veld')],
                                                default='OD', max_length=2)),
                ('log', models.TextField(blank=True, default='')),
                ('boog_type', models.ForeignKey(on_delete=PROTECT, to='BasisTypen.boogtype')),
                ('door_account', models.ForeignKey(on_delete=PROTECT, to='Account.account')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=PROTECT, blank=True, null=True,
                                                      to='BasisTypen.leeftijdsklasse')),
                ('voor_sporter', models.ForeignKey(on_delete=CASCADE, to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(blank=True, null=True, on_delete=PROTECT, to='Wedstrijden.wedstrijd')),
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
                ('soort_bijlage', models.CharField(choices=[('s', 'Scorebriefje'), ('u', 'Uitslag')],
                                                   default='s', max_length=1)),
                ('bestandstype', models.CharField(choices=[('f', 'Foto'), ('p', 'PDF'), ('?', '?')],
                                                  default='f', max_length=1)),
                ('log', models.TextField(blank=True, default='')),
                ('aanvraag', models.ForeignKey(on_delete=CASCADE, to='Spelden.speldaanvraag')),
            ],
            options={
                'verbose_name': 'Speld bijlage',
                'verbose_name_plural': 'Speld bijlagen',
            },
        ),
    ]

# end of file
