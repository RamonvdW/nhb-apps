# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.definities import GESLACHT_ALLE, ORGANISATIE_VETERANEN, BOOGTYPE_AFKORTING_RECURVE


LEEFTIJDSKLASSEN = (
    # WA + KHSN + KHSN-Veteranen
    # volgorde afk    geslacht        min max  kort        beschrijving      organisatie

    # Veteranen
    (70,       'VAL', GESLACHT_ALLE,  50, 0,   '50+',      '50+ jaar',       ORGANISATIE_VETERANEN),
    (71,       'V50', GESLACHT_ALLE,  50, 54,  '50-54',    '50 t/m 54 jaar', ORGANISATIE_VETERANEN),
    (72,       'V55', GESLACHT_ALLE,  55, 59,  '55-59',    '55 t/m 59 jaar', ORGANISATIE_VETERANEN),
    (73,       'V60', GESLACHT_ALLE,  60, 64,  '60-64',    '60 t/m 64 jaar', ORGANISATIE_VETERANEN),
    (74,       'V65', GESLACHT_ALLE,  65, 69,  '65-69',    '65 t/m 69 jaar', ORGANISATIE_VETERANEN),
    (75,       'V70', GESLACHT_ALLE,  70, 74,  '70-74',    '70 t/m 74 jaar', ORGANISATIE_VETERANEN),
    (76,       'V75', GESLACHT_ALLE,  75, 79,  '75-79',    '75 t/m 79 jaar', ORGANISATIE_VETERANEN),
    (77,       'V80', GESLACHT_ALLE,  80, 0,   '80+',      '80+ jaar',       ORGANISATIE_VETERANEN),
)

KALENDERWEDSTRIJDENKLASSEN = (
    # nr  boog  lkl    afk     beschrijving
    (170, 'R',  'V50', 'RV50', 'Recurve Veteranen 50 t/m 54 jaar'),
    (171, 'R',  'V55', 'RV55', 'Recurve Veteranen 55 t/m 59 jaar'),
    (172, 'R',  'V60', 'RV60', 'Recurve Veteranen 60 t/m 64 jaar'),
    (173, 'R',  'V65', 'RV65', 'Recurve Veteranen 65 t/m 69 jaar'),
    (174, 'R',  'V70', 'RV70', 'Recurve Veteranen 70 t/m 74 jaar'),
    (175, 'R',  'V75', 'RV75', 'Recurve Veteranen 75 t/m 79 jaar'),
    (176, 'R',  'V80', 'RV80', 'Recurve Veteranen 80+ jaar'),

    (180, 'C',  'VAL', 'CVAL', 'Compound Veteranen 50+ jaar'),
    (181, 'BB', 'VAL', 'BVAL', 'Barebow Veteranen 50+ jaar'),
    (182, 'TR', 'VAL', 'TVAL', 'Traditional Veteranen 50+ jaar'),
    (183, 'LB', 'VAL', 'LVAL', 'Longbow Veteranen 50+ jaar'),
)


def init_veteranen_klassen(apps, _):
    """ Maak de KHSN veteranen kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'Leeftijdsklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # haal de bogen en leeftijden op en sorteer meteen op de gewenste volgorde
    boog_r = boogtype_klas.objects.get(afkorting=BOOGTYPE_AFKORTING_RECURVE)

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
    for volgorde, _, lkl, afkorting, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        leeftijdsklasse = leeftijdsklasse_klas.objects.get(afkorting=lkl)

        obj = kalenderwedstrijdklasse_klas(
                        beschrijving=beschrijving,
                        boogtype=boog_r,
                        leeftijdsklasse=leeftijdsklasse,
                        volgorde=volgorde,
                        afkorting=afkorting,
                        organisatie=ORGANISATIE_VETERANEN)
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
        migrations.AlterField(
            model_name='boogtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA'), ('S', 'WA strikt'), ('V', 'KHSN veteranen')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='kalenderwedstrijdklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA'), ('S', 'WA strikt'), ('V', 'KHSN veteranen')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='leeftijdsklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA'), ('S', 'WA strikt'), ('V', 'KHSN veteranen')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='teamtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'KHSN'), ('F', 'IFAA'), ('S', 'WA strikt'), ('V', 'KHSN veteranen')], default='W', max_length=1),
        ),
        migrations.RunPython(init_veteranen_klassen),
    ]

# end of file
