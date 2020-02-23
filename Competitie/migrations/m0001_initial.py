# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    initial = True
    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('BasisTypen', 'm0002_basistypen_2018'),
        ('NhbStructuur', 'm0003_nhbstructuur_2019'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Competitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=40)),
                ('afstand', models.CharField(choices=[('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
                ('begin_jaar', models.PositiveSmallIntegerField()),
                ('uiterste_datum_lid', models.DateField()),
                ('begin_aanmeldingen', models.DateField()),
                ('einde_aanmeldingen', models.DateField()),
                ('einde_teamvorming', models.DateField()),
                ('eerste_wedstrijd', models.DateField()),
                ('is_afgesloten', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DeelCompetitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('laag', models.CharField(choices=[('Regio', 'Regiocompetitie'), ('RK', 'Rayoncompetitie'), ('BK', 'Bondscompetitie')], max_length=5)),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Competitie.Competitie')),
                ('functies', models.ManyToManyField(to='auth.Group')),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieWedstrijdKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('wedstrijdklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.WedstrijdKlasse')),
            ],
        ),
        migrations.AddField(
            model_name='competitie',
            name='klassen_indiv',
            field=models.ManyToManyField(related_name='indiv', to='Competitie.CompetitieWedstrijdKlasse'),
        ),
        migrations.AddField(
            model_name='competitie',
            name='klassen_team',
            field=models.ManyToManyField(related_name='team', to='Competitie.CompetitieWedstrijdKlasse'),
        ),
    ]

# end of file
