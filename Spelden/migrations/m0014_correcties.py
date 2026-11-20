# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

SPELD_DISCIPLINE_NVT = 'XX'


from django.db import migrations, models
from BasisTypen.definities import ORGANISATIE_WA
from Spelden.definities import SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR, SPELD_DISCIPLINE_VELD


def maak_voorwaarden_wa_zilveren_ster_recurve_hoog(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_r = boog_klas.objects.get(afkorting='R')

    # corrigeer volgorde voor zilver ster recurve 1350 en 1400
    speld_klas.objects.filter(volgorde=1204, pas_code="R1350Z").update(volgorde=1205)
    speld_klas.objects.filter(volgorde=1204, pas_code="R1400Z").update(volgorde=1206)

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(1205, 1206)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA,
                                       volgorde__in=(21, 22, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    soort = "1440-ronde"
    bulk = list()

    # maak de voorwaarden aan voor de zilveren ster recurve 1350 en 1400
    for volgorde, afstanden in (
            (51, "60, 50, 40, 30"),     # 51=MV: 50+ dames
            (52, "70, 60, 50, 30"),     # 52=MH: 50+ heren
            (21, "60, 50, 40, 30"),     # 21=CV: Onder 18 dames
            (22, "70, 60, 50, 30")):    # 22=CH: Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_r,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1205, 1350),       # 1350 zilveren ster, recurve
                                    (1206, 1400)]       # 1300 zilveren ster, recurve
        ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_wa_zilveren_ster_compound_hoog(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_c = boog_klas.objects.get(afkorting='C')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(1215, 1216)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA, volgorde__in=(21, 22, 51, 52)):
        lkls[lkl.volgorde] = lkl
    # for

    soort = "1440-ronde"
    bulk = list()

    # compound zilveren ster
    for volgorde, afstanden in (
            (51, "60, 50, 40, 30"),     # 51=MV: 50+ dames
            (52, "70, 60, 50, 30"),     # 52=MH: 50+ heren
            (21, "60, 50, 40, 30"),     # 21=CV: Onder 18 dames
            (22, "70, 60, 50, 30")):    # 22=CH: Onder 18 heren

        lkl = lkls[volgorde]

        bulk.extend([
            voorwaarden_klas(
                speld=spelden[speld_nr],
                discipline=SPELD_DISCIPLINE_OUTDOOR,
                wedstrijd_soort=soort,
                leeftijdsklasse=lkl,
                boog_type=boog_c,
                afstanden=afstanden,
                aantal_pijlen=4*36,
                benodigde_score=score)

            for speld_nr, score in [(1215, 1350),  # 1350 zilveren ster, compound
                                    (1216, 1400)]  # 1400 zilveren ster, compound
        ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


def maak_voorwaarden_target_awards_18m_ronde_compound(apps, _):
    # haal de klassen op die van toepassing zijn op het moment van migratie
    speld_klas = apps.get_model('Spelden', 'Speld')
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')
    boog_klas = apps.get_model('BasisTypen', 'BoogType')
    lkl_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')

    boog_c = boog_klas.objects.get(afkorting='C')

    spelden = dict()
    for speld in speld_klas.objects.filter(volgorde__in=(3001, 3002, 3003, 3004, 3005, 3006)):
        spelden[speld.volgorde] = speld
    # for

    lkls = dict()
    for lkl in lkl_klas.objects.filter(organisatie=ORGANISATIE_WA,
                                       volgorde__in=(31, 32, 41, 42)):
        lkls[lkl.volgorde] = lkl
    # for

    bulk = list()

    # 18m ronde (compound)
    soort = '18m ronde'
    for volgorde in (
            41,     # Senioren dames
            42,     # Senioren heren
            31,     # Onder 21 dames
            32):    # Onder 21 heren

        lkl = lkls[volgorde]
        afstanden = "18"
        aantal_pijlen = 2*30

        for discipline in (SPELD_DISCIPLINE_OUTDOOR, SPELD_DISCIPLINE_INDOOR):
            bulk.extend([
                voorwaarden_klas(
                    speld=spelden[3001],        # wit
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=500),
                voorwaarden_klas(
                    speld=spelden[3002],        # zwart
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=525),
                voorwaarden_klas(
                    speld=spelden[3003],        # blauw
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=550),
                voorwaarden_klas(
                    speld=spelden[3004],        # rood
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=575),
                voorwaarden_klas(
                    speld=spelden[3005],        # goud
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=585),
                voorwaarden_klas(
                    speld=spelden[3006],        # purper
                    discipline=discipline,
                    wedstrijd_soort=soort,
                    leeftijdsklasse=lkl,
                    boog_type=boog_c,
                    afstanden=afstanden,
                    aantal_pijlen=aantal_pijlen,
                    benodigde_score=595),
            ])
    # for

    voorwaarden_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Spelden', 'm0013_graadspelden'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='speldaanvraag',
            name='score_sm',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(maak_voorwaarden_wa_zilveren_ster_recurve_hoog, migrations.RunPython.noop),
        migrations.RunPython(maak_voorwaarden_wa_zilveren_ster_compound_hoog, migrations.RunPython.noop),
        migrations.RunPython(maak_voorwaarden_target_awards_18m_ronde_compound, migrations.RunPython.noop),
    ]

# end of file
