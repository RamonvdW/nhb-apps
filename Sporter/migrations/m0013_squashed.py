# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import Sporter.models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Sporter', 'm0010_squashed'),
                ('Sporter', 'm0011_geboorteplaats_telefoon'),
                ('Sporter', 'm0012_sporterboog_ordering')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0049_squashed'),
        ('NhbStructuur', 'm0027_squashed'),
        ('Account', 'm0023_squashed'),
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
                ('account', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('adres_code', models.CharField(blank=True, default='', max_length=30)),
            ],
            options={
                'verbose_name': 'Sporter',
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
                ('wedstrijd_geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], default='M', max_length=1)),
                ('wedstrijd_geslacht_gekozen', models.BooleanField(default=True)),
                ('sporter', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
                ('para_met_rolstoel', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Sporter voorkeuren',
                'verbose_name_plural': 'Sporter voorkeuren',
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
            },
        ),
        migrations.CreateModel(
            name='Secretaris',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sporter', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to='Sporter.sporter')),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Secretaris Vereniging',
                'verbose_name_plural': 'Secretaris Vereniging',
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
            ],
            options={
                'verbose_name': 'Speelsterkte',
            },
        ),
        migrations.AddIndex(
            model_name='sporterboog',
            index=models.Index(fields=['voor_wedstrijd'], name='Sporter_spo_voor_we_c6b357_idx'),
        ),
        migrations.AddField(
            model_name='sporter',
            name='geboorteplaats',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='sporter',
            name='telefoon',
            field=models.CharField(blank=True, default='', max_length=25),
        ),
        migrations.AlterModelOptions(
            name='sporterboog',
            options={'ordering': ['sporter__lid_nr', 'boogtype__volgorde'], 'verbose_name': 'SporterBoog', 'verbose_name_plural': 'SporterBoog'},
        ),
    ]

# end of file
