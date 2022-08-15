# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Score.models import AG_DOEL_INDIV, AG_DOEL_TEAM

SCORE_TYPE_INDIV_AG = 'I'       # voor de bondscompetities
SCORE_TYPE_TEAM_AG = 'T'        # voor de bondscompetities


def migreer_ag(apps, _):
    """ Migreer de aanvangsgemiddelden en geschiedenis van Score/ScoreHist naar de nieuwe records """

    # haal de klassen op die van toepassing zijn vóór de migratie
    ag_klas = apps.get_model('Score', 'Aanvangsgemiddelde')
    score_klas = apps.get_model('Score', 'Score')
    ag_hist_klas = apps.get_model('Score', 'AanvangsgemiddeldeHist')
    score_hist_klas = apps.get_model('Score', 'ScoreHist')

    # stap 1: vertaal relevante Score naar Aanvangsgemiddelde

    bulk = list()
    score2ag = dict()       # [score.pk] = Aanvangsgemiddelde()
    for score in (score_klas
                  .objects
                  .filter(type__in=(SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG))
                  .select_related('sporterboog',
                                  'sporterboog__boogtype')):        # pragma: no cover

        doel = AG_DOEL_INDIV if score.type == SCORE_TYPE_INDIV_AG else AG_DOEL_TEAM

        ag = ag_klas(
                doel=doel,
                waarde=score.waarde / 1000.0,       # AG was opgeslagen x 1000
                boogtype=score.sporterboog.boogtype,
                sporterboog=score.sporterboog,
                afstand_meter=score.afstand_meter)
        score2ag[score.pk] = ag

        bulk.append(ag)

        if len(bulk) == 500:
            ag_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    ag_klas.objects.bulk_create(bulk)
    del bulk

    # stap 2: vertaal relevante ScoreHist naar AanvangsgemiddeldeHist

    bulk = list()
    for score_hist in (score_hist_klas
                       .objects
                       .select_related('score',
                                       'door_account')
                       .filter(score__type__in=(SCORE_TYPE_INDIV_AG,
                                                SCORE_TYPE_TEAM_AG))):     # pragma: no cover

        ag = score2ag[score_hist.score.pk]

        ag_hist = ag_hist_klas(
                        when=score_hist.when,
                        ag=ag,
                        oude_waarde=score_hist.oude_waarde / 1000.0,        # AG was opgeslagen x 1000
                        nieuwe_waarde=score_hist.nieuwe_waarde / 1000.0,    # AG was opgeslagen x 1000
                        door_account=score_hist.door_account,
                        notitie=score_hist.notitie)

        bulk.append(ag_hist)
        if len(bulk) == 500:
            ag_hist_klas.objects.bulk_create(bulk)
            bulk = list()
    # for

    ag_hist_klas.objects.bulk_create(bulk)
    del bulk

    # stap 3: verwijder omgezetten ScoreHist en Score

    del_qset = score_klas.objects.filter(type__in=(SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG))
    del_qset.delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0021_squashed'),
        ('BasisTypen', 'm0046_wkl_refresh'),
        ('Sporter', 'm0011_geboorteplaats_telefoon'),
        ('Score', 'm0017_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Aanvangsgemiddelde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doel', models.CharField(choices=[('i', 'Individueel'), ('t', 'Teamcompetitie')], default='i', max_length=1)),
                ('waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
            ],
        ),
        migrations.CreateModel(
            name='AanvangsgemiddeldeHist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('oude_waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('nieuwe_waarde', models.DecimalField(decimal_places=3, max_digits=6)),
                ('notitie', models.CharField(max_length=100)),
                ('ag', models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, related_name='ag_hist', to='Score.aanvangsgemiddelde')),
                ('door_account', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to='Account.account')),
            ],
        ),
        migrations.AddIndex(
            model_name='aanvangsgemiddeldehist',
            index=models.Index(fields=['when'], name='Score_aanva_when_9de5cf_idx'),
        ),
        migrations.RunPython(migreer_ag),
        migrations.AlterField(
            model_name='score',
            name='type',
            field=models.CharField(choices=[('S', 'Score'), ('G', 'Geen score')], default='S', max_length=1),
        ),
    ]

# end of file
