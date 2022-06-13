# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def maak_kalenderwedstrijdklassen_ifaa(apps, _):
    """ Maak de IFAA kalender wedstrijdklassen aan """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    ifaa = 'F'  # International Field Archery Association

    # haal de bogen en leeftijden op en sorteer meteen op de gewenste volgorde
    bogen = boogtype_klas.objects.filter(organisatie=ifaa).order_by('volgorde')
    leeftijden = leeftijdsklasse_klas.objects.filter(organisatie=ifaa).order_by('-volgorde')

    # maak elke combinatie van leeftijdsklassen en boogtype aan
    bulk = list()
    groep_volgorde = 1000
    for boog in bogen:
        volgorde = groep_volgorde
        for leeftijd in leeftijden:
            beschrijving = '%s %s' % (boog.beschrijving, leeftijd.beschrijving)

            bulk.append(
                kalenderwedstrijdklasse_klas(
                    organisatie=ifaa,
                    beschrijving=beschrijving,
                    boogtype=boog,
                    leeftijdsklasse=leeftijd,
                    volgorde=volgorde)
            )
            volgorde += 1
        # for

        groep_volgorde += 100
    # for

    kalenderwedstrijdklasse_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0037_ifaa_leeftijdsklassen'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_kalenderwedstrijdklassen_ifaa),
    ]

# end of file
