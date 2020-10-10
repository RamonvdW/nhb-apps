# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


# TODO: kan deze migratiefunctie weg?
def maak_taken(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    taken_klas = apps.get_model('Competitie', 'CompetitieTaken')

    taken = taken_klas()
    taken.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0010_squashed'),
        ('Functie', 'm0008_squashed'),
        ('NhbStructuur', 'm0015_squashed'),
        ('Schutter', 'm0006_squashed'),
        ('Score', 'm0005_squashed'),
        ('Wedstrijden', 'm0006_squashed'),
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
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.Competitie')),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbRegio')),
                ('functie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Functie.Functie')),
                ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdenPlan')),
                ('inschrijf_methode', models.CharField(choices=[('1', 'Kies wedstrijden'), ('2', 'Naar locatie wedstrijdklasse'), ('3', 'Voorkeur dagdelen')], default='2', max_length=1)),
                ('toegestane_dagdelen', models.CharField(blank=True, default='', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.Competitie')),
                ('indiv', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.IndivWedstrijdklasse')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.TeamWedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Competitie klasse',
                'verbose_name_plural': 'Competitie klassen',
            },
        ),
        migrations.CreateModel(
            name='RegioCompetitieSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_handmatig_ag', models.BooleanField(default=False)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('score1', models.PositiveIntegerField(default=0)),
                ('score2', models.PositiveIntegerField(default=0)),
                ('score3', models.PositiveIntegerField(default=0)),
                ('score4', models.PositiveIntegerField(default=0)),
                ('score5', models.PositiveIntegerField(default=0)),
                ('score6', models.PositiveIntegerField(default=0)),
                ('score7', models.PositiveIntegerField(default=0)),
                ('totaal', models.PositiveIntegerField(default=0)),
                ('laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('bij_vereniging', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.CompetitieKlasse')),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Schutter.SchutterBoog')),
                ('inschrijf_notitie', models.TextField(blank=True, default='')),
                ('inschrijf_voorkeur_dagdeel', models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"), ('ZA', 'Zaterdag'), ('ZO', 'Zondag'), ('WE', 'Weekend')], default='GN', max_length=2)),
                ('inschrijf_voorkeur_team', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
                ('alt_gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('alt_laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('alt_score1', models.PositiveIntegerField(default=0)),
                ('alt_score2', models.PositiveIntegerField(default=0)),
                ('alt_score3', models.PositiveIntegerField(default=0)),
                ('alt_score4', models.PositiveIntegerField(default=0)),
                ('alt_score5', models.PositiveIntegerField(default=0)),
                ('alt_score6', models.PositiveIntegerField(default=0)),
                ('alt_score7', models.PositiveIntegerField(default=0)),
                ('alt_totaal', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Regiocompetitie Schutterboog',
                'verbose_name_plural': 'Regiocompetitie Schuttersboog',
            },
        ),
        migrations.CreateModel(
            name='DeelcompetitieRonde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_nr', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=40)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbCluster')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.DeelCompetitie')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdenPlan')),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_scorehist', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Score.ScoreHist')),
            ],
        ),
        migrations.RunPython(maak_taken),
    ]

# end of file
