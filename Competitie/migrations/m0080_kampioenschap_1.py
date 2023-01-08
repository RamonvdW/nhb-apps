# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Competitie.models import DEEL_RK, DEEL_BK

# old
LAAG_RK = 'RK'
LAAG_BK = 'BK'


def maak_deelkampioenschappen(apps, _):     # pragma: no cover
    """ maak de nieuwe DeelKampioenschappen aan voor de lopende competities """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    deelcomp_klas = apps.get_model('Competitie', 'DeelCompetitie')
    deelkamp_klas = apps.get_model('Competitie', 'DeelKampioenschap')

    bulk = list()
    for deelcomp in deelcomp_klas.objects.filter(laag__in=(LAAG_RK, LAAG_BK)).order_by('laag', 'nhb_rayon__rayon_nr'):

        if deelcomp.laag == LAAG_RK:
            kamp = deelkamp_klas(
                        deel=DEEL_RK,
                        competitie=deelcomp.competitie,
                        nhb_rayon=deelcomp.nhb_rayon,
                        functie=deelcomp.functie,
                        heeft_deelnemerslijst=deelcomp.heeft_deelnemerslijst,
                        old_deelcomp=deelcomp)
            bulk.append(kamp)
        else:
            # BK
            kamp = deelkamp_klas(
                        deel=DEEL_BK,
                        competitie=deelcomp.competitie,
                        functie=deelcomp.functie,
                        heeft_deelnemerslijst=deelcomp.heeft_deelnemerslijst,
                        old_deelcomp=deelcomp)
            bulk.append(kamp)
    # for

    deelkamp_klas.objects.bulk_create(bulk)

    # neem nu alle matches over
    for deelkamp in deelkamp_klas.objects.select_related('old_deelcomp').prefetch_related('old_deelcomp__rk_bk_matches').all():
        deelkamp.rk_bk_matches.set(deelkamp.old_deelcomp.rk_bk_matches.all())
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0016_rol_mww'),
        ('Competitie', 'm0079_rename_schutter'),
        ('NhbStructuur', 'm0030_bondsbureau'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='DeelKampioenschap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deel', models.CharField(choices=[('RK', 'RK'), ('BK', 'BK')], max_length=2)),
                ('is_klaar_indiv', models.BooleanField(default=False)),
                ('is_klaar_teams', models.BooleanField(default=False)),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('heeft_deelnemerslijst', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('functie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Functie.functie')),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
                ('rk_bk_matches', models.ManyToManyField(blank=True, to='Competitie.competitiematch')),
                ('old_deelcomp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie', null=True)),
            ],
            options={
                'verbose_name': 'Deel kampioenschap',
                'verbose_name_plural': 'Deel kampioenschappen',
            },
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='kampioenschap',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    to='Competitie.deelkampioenschap'),
        ),
        migrations.RunPython(maak_deelkampioenschappen, reverse_code=migrations.RunPython.noop)
    ]

# end of file
