# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import Sporter.models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0057_squashed'),
        ('Vereniging', 'm0006_squashed1'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Sporter',
            fields=[
                ('lid_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('voornaam', models.CharField(max_length=100)),
                ('achternaam', models.CharField(max_length=100)),
                ('unaccented_naam', models.CharField(blank=True, default='', max_length=200)),
                ('email', models.CharField(max_length=150)),
                ('geboorte_datum', models.DateField(validators=[Sporter.models.validate_geboorte_datum])),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('X', 'Anders')], max_length=1)),
                ('para_classificatie', models.CharField(blank=True, max_length=30)),
                ('is_actief_lid', models.BooleanField(default=True)),
                ('sinds_datum', models.DateField(validators=[Sporter.models.validate_sinds_datum])),
                ('lid_tot_einde_jaar', models.PositiveSmallIntegerField(default=0)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                              to='Account.account')),
                ('adres_code', models.CharField(blank=True, default='', max_length=30)),
                ('postadres_1', models.CharField(blank=True, default='', max_length=100)),
                ('postadres_2', models.CharField(blank=True, default='', max_length=100)),
                ('postadres_3', models.CharField(blank=True, default='', max_length=100)),
                ('is_erelid', models.BooleanField(default=False)),
                ('geboorteplaats', models.CharField(blank=True, default='', max_length=100)),
                ('telefoon', models.CharField(blank=True, default='', max_length=25)),
                ('wa_id', models.CharField(blank=True, default='', max_length=8)),
                ('is_gast', models.BooleanField(default=False)),
                ('is_overleden', models.BooleanField(default=False)),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                                     to='Vereniging.vereniging')),
                ('scheids', models.CharField(blank=True, choices=[('N', 'Niet'), ('B', 'Bondsscheidsrechter'),
                                                                  ('V', 'Verenigingsscheidsrechter'),
                                                                  ('I', 'Internationaal Scheidsrechter')],
                                             default='N', max_length=2)),
                ('adres_lat', models.CharField(blank=True, default='', max_length=10)),
                ('adres_lon', models.CharField(blank=True, default='', max_length=10)),
            ],
            options={
                'verbose_name': 'Sporter',
            },
        ),
        migrations.CreateModel(
            name='SporterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heeft_interesse', models.BooleanField(default=True)),
                ('voor_wedstrijd', models.BooleanField(default=False)),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.CASCADE, to='BasisTypen.boogtype')),
                ('sporter', models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'SporterBoog',
                'verbose_name_plural': 'SporterBoog',
                'unique_together': {('sporter', 'boogtype')},
                'ordering': ['sporter__lid_nr', 'boogtype__volgorde'],
                'indexes': [models.Index(fields=['voor_wedstrijd'], name='Sporter_spo_voor_we_c6b357_idx')],
            },
        ),
        migrations.CreateModel(
            name='Speelsterkte',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('beschrijving', models.CharField(max_length=50)),
                ('discipline', models.CharField(max_length=50)),
                ('category', models.CharField(max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField()),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('pas_code', models.CharField(blank=True, default='', max_length=10)),
            ],
            options={
                'verbose_name': 'Speelsterkte',
            },
        ),
        migrations.CreateModel(
            name='SporterVoorkeuren',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voorkeur_eigen_blazoen', models.BooleanField(default=False)),
                ('voorkeur_meedoen_competitie', models.BooleanField(default=True)),
                ('opmerking_para_sporter', models.CharField(blank=True, default='', max_length=256)),
                ('voorkeur_discipline_25m1pijl', models.BooleanField(default=True)),
                ('voorkeur_discipline_outdoor', models.BooleanField(default=True)),
                ('voorkeur_discipline_indoor', models.BooleanField(default=True)),
                ('voorkeur_discipline_clout', models.BooleanField(default=True)),
                ('voorkeur_discipline_veld', models.BooleanField(default=True)),
                ('voorkeur_discipline_run', models.BooleanField(default=True)),
                ('voorkeur_discipline_3d', models.BooleanField(default=True)),
                ('wedstrijd_geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')],
                                                        default='M', max_length=1)),
                ('wedstrijd_geslacht_gekozen', models.BooleanField(default=True)),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('para_voorwerpen', models.BooleanField(default=False)),
                ('scheids_opt_in_korps_email', models.BooleanField(default=False)),
                ('scheids_opt_in_korps_tel_nr', models.BooleanField(default=False)),
                ('scheids_opt_in_ver_email', models.BooleanField(default=False)),
                ('scheids_opt_in_ver_tel_nr', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Sporter voorkeuren',
                'verbose_name_plural': 'Sporter voorkeuren',
            },
        ),
    ]

# end of file
