# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.definities import GESLACHT_ALLE, ORGANISATIE_KHSN, BOOGTYPE_AFKORTING_RECURVE


LEEFTIJDSKLASSEN = (
    # WA + KHSN
    # volgorde afk    geslacht        min max  kort        beschrijving      organisatie

    # Veteranen
    (70,       'VAL', GESLACHT_ALLE,  50, 0,   '50+',      '50+ jaar',       ORGANISATIE_KHSN),
    (71,       'V50', GESLACHT_ALLE,  50, 54,  '50-54',    '50 t/m 54 jaar', ORGANISATIE_KHSN),
    (72,       'V55', GESLACHT_ALLE,  55, 59,  '55-59',    '55 t/m 59 jaar', ORGANISATIE_KHSN),
    (73,       'V60', GESLACHT_ALLE,  60, 64,  '60-64',    '60 t/m 64 jaar', ORGANISATIE_KHSN),
    (74,       'V65', GESLACHT_ALLE,  65, 69,  '65-69',    '65 t/m 69 jaar', ORGANISATIE_KHSN),
    (75,       'V70', GESLACHT_ALLE,  70, 74,  '70-74',    '70 t/m 74 jaar', ORGANISATIE_KHSN),
    (76,       'V75', GESLACHT_ALLE,  75, 79,  '75-79',    '75 t/m 79 jaar', ORGANISATIE_KHSN),
    (77,       'V80', GESLACHT_ALLE,  80, 0,   '80+',      '80+ jaar',       ORGANISATIE_KHSN),
)

KALENDERWEDSTRIJDENKLASSEN = (
    # nr  boog  lkl    afk     beschrijving
    (701, 'R',  'VAL', 'RVAL',   'Veteranen 50+ Recurve'),
    (702, 'C',  'VAL', 'CVAL',   'Veteranen 50+ Compound'),
    (703, 'BB', 'VAL', 'BVAL',   'Veteranen 50+ Barebow'),
    (704, 'TR', 'VAL', 'TVAL',   'Veteranen 50+ Traditional'),
    (705, 'LB', 'VAL', 'LVAL',   'Veteranen 50+ Longbow'),

    (710, 'R',  'V50', 'RV50',   'Veteranen 50 t/m 54 Recurve'),
    (711, 'R',  'V55', 'RV55',   'Veteranen 55 t/m 59 Recurve'),
    (712, 'R',  'V60', 'RV60',   'Veteranen 60 t/m 64 Recurve'),
    (713, 'R',  'V65', 'RV65',   'Veteranen 65 t/m 69 Recurve'),
    (714, 'R',  'V70', 'RV70',   'Veteranen 70 t/m 74 Recurve'),
    (715, 'R',  'V75', 'RV75',   'Veteranen 75 t/m 79 Recurve'),
    (716, 'R',  'V80', 'RV80',   'Veteranen 80+ Recurve'),
)


def init_veteranen_klassen(apps, _):
    """ Maak de KHSN veteranen kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    bulk = list()
    for volgorde, afkorting, geslacht, leeftijd_min, leeftijd_max, kort, beschrijving, organisatie in LEEFTIJDSKLASSEN:
        lkl = leeftijdsklasse_klas(
                    afkorting=afkorting,
                    wedstrijd_geslacht=geslacht,
                    klasse_kort=kort,
                    beschrijving=beschrijving,
                    volgorde=volgorde,
                    min_wedstrijdleeftijd=leeftijd_min,
                    max_wedstrijdleeftijd=leeftijd_max,
                    organisatie=organisatie)
        bulk.append(lkl)
    # for
    leeftijdsklasse_klas.objects.bulk_create(bulk)

    bulk = list()
    for volgorde, boog_afk, lkl, afkorting, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        leeftijdsklasse = leeftijdsklasse_klas.objects.get(afkorting=lkl)
        boogtype = boogtype_klas.objects.get(afkorting=boog_afk)

        obj = kalenderwedstrijdklasse_klas(
                        beschrijving=beschrijving,
                        boogtype=boogtype,
                        leeftijdsklasse=leeftijdsklasse,
                        volgorde=volgorde,
                        afkorting=afkorting,
                        organisatie=leeftijdsklasse.organisatie)
        bulk.append(obj)
    # for
    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0062_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_veteranen_klassen),
    ]

# end of file
