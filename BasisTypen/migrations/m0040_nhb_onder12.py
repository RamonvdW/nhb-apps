# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import ORGANISATIE_NHB


KALENDERWEDSTRIJDENKLASSEN = (
    (160, 'R', 'AA1', 'Recurve Onder 12 (aspirant)'),
    (161, 'R', 'AH1', 'Recurve Onder 12 jongens (aspirant)'),
    (162, 'R', 'AV1', 'Recurve Onder 12 meisjes (aspirant)'),


    (260, 'C', 'AA1', 'Compound Onder 12 (aspirant)'),
    (261, 'C', 'AH1', 'Compound Onder 12 jongens (aspirant)'),
    (262, 'C', 'AV1', 'Compound Onder 12 meisjes (aspirant)'),


    (360, 'BB', 'AA1', 'Barebow Onder 12 (aspirant)'),
    (361, 'BB', 'AH1', 'Barebow Onder 12 jongens (aspirant)'),
    (362, 'BB', 'AV1', 'Barebow Onder 12 meisjes (aspirant)'),


    (560, 'TR', 'AA1', 'Traditional Onder 12 (aspirant)'),
    (561, 'TR', 'AH1', 'Traditional Onder 12 jongens (aspirant)'),
    (562, 'TR', 'AV1', 'Traditional Onder 12 meisjes (aspirant)'),


    (660, 'LB', 'AA1', 'Longbow Onder 12 (aspirant)'),
    (661, 'LB', 'AH1', 'Longbow Onder 12 jongens (aspirant)'),
    (662, 'LB', 'AV1', 'Longbow Onder 12 meisjes (aspirant)'),
)


def maak_kalender_wedstrijdklassen_nhb_onder_12(apps, _):
    """ Voeg wedstrijdklassen toe aan de Kalender voor Onder 12 """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    afk2boog = dict()  # [afkorting] = BoogType
    for boog in boogtype_klas.objects.all():
        afk2boog[boog.afkorting] = boog
    # for

    afk2lkl = dict()  # [afkorting] = LeeftijdsKlasse
    for lkl in leeftijdsklasse_klas.objects.all():
        afk2lkl[lkl.afkorting] = lkl
    # for

    bulk = list()
    for volgorde, boog_afk, lkl_afk, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        boog = afk2boog[boog_afk]
        lkl = afk2lkl[lkl_afk]
        obj = kalenderwedstrijdklasse_klas(
                    organisatie=ORGANISATIE_NHB,
                    beschrijving=beschrijving,
                    boogtype=boog,
                    leeftijdsklasse=lkl,
                    volgorde=volgorde)
        bulk.append(obj)
    # for
    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


def corrigeer_kalender_wedstrijdklasse_beschrijving(apps, _):
    """ Corrigeer de beschrijving van wedstrijdklasse 551 """

    # fout: 'Traditional Onder 14 14 jongens (aspirant)'

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')

    obj = kalenderwedstrijdklasse_klas.objects.get(volgorde=551)
    obj.beschrijving = 'Traditional Onder 14 jongens (aspirant)'
    obj.save(update_fields=['beschrijving'])


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0039_ifaa_afkortingen'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_kalender_wedstrijdklassen_nhb_onder_12),
        migrations.RunPython(corrigeer_kalender_wedstrijdklasse_beschrijving)
    ]

# end of file
