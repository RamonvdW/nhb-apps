# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def neem_wedstrijdklasse_buiten_gebruik(apps, beschrijving):
    """ neem een WedstrijdKlasse buiten gebruik, want ivm verwijzingen vanuit andere tabellen
        is het niet mogelijk om de klasse ook echt te verwijderen
    """
    wedstrijdklasse_klas = apps.get_model('BasisTypen', 'WedstrijdKlasse')

    for wkl in wedstrijdklasse_klas.objects.filter(beschrijving=beschrijving, buiten_gebruik=False):
        wkl.buiten_gebruik = True
        wkl.save()
    # for


def create_wedstrijdklasse_individueel(apps, beschrijving, boogtypen, leeftijdsklassen, niet_voor_rk_bk=False):
    """ Maak de wedstrijdklassen aan
        Koppel de gewenste boogtypen en leeftijdsklassen aan de wedstrijdklasse
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    wedstrijdklasse_klas = apps.get_model('BasisTypen', 'WedstrijdKlasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')
    wedstrijdklasseleeftijd_klas = apps.get_model('BasisTypen', 'WedstrijdKlasseLeeftijd')
    wedstrijdklasseboog_klas = apps.get_model('BasisTypen', 'WedstrijdKlasseBoog')

    wkl = wedstrijdklasse_klas(
            buiten_gebruik=False,
            beschrijving=beschrijving,
            is_voor_teams=False,
            niet_voor_rk_bk=niet_voor_rk_bk)
    wkl.save()

    # doorloop alle boogtypen en koppel deze aan de nieuwe wedstrijdklasse
    # door een wedstrijdklasseboog record aan te maken
    for rec in boogtype_klas.objects.all():
        if rec.afkorting in boogtypen:
            wedstrijdklasseboog_klas(boogtype=rec, wedstrijdklasse=wkl).save()
    # for

    # doorloop alle leeftijdsklassen en koppel deze aan de nieuwe wedstrijdklasse
    # door een wedstrijdklasseleeftijd record aan te maken
    for rec in leeftijdsklasse_klas.objects.all():
        if rec.afkorting in leeftijdsklassen:
            wedstrijdklasseleeftijd_klas(leeftijdsklasse=rec, wedstrijdklasse=wkl).save()
    # for


def wijzig_wedstrijdklassen_hout_jeugd(apps, schema_editor):
    # wijzig de wedstrijdklassen jaar 2018 volgens spec v1.2, tabel 2.4
    #   naar de wedstrijdklassen jaar 2019 volgens spec v1.3, tabel 2.4

    # gewijzigde en nieuwe klassen:
    WKL_INDIV = (
        ('Barebow klasse 1',                       ('BB',), ('SH', 'SV')),
        ('Barebow klasse 2',                       ('BB',), ('SH', 'SV')),
        ('Barebow Jeugd klasse 1',                 ('BB',), ('JH', 'JV', 'CH', 'CV')),
        ('Barebow Aspiranten < 11 jaar',           ('BB',), ('AH1', 'AV1'), True),
        ('Barebow Aspiranten 11-12 jaar',          ('BB',), ('AH2', 'AV2'), True),

        ('Instinctive Bow klasse 1',               ('IB',), ('SH', 'SV')),
        ('Instinctive Bow klasse 2',               ('IB',), ('SH', 'SV')),
        ('Instinctive Bow Jeugd klasse 1',         ('IB',), ('JH', 'JV', 'CH', 'CV')),
        ('Instinctive Bow Aspiranten < 11 jaar',   ('IB',), ('AH1', 'AV1'), True),
        ('Instinctive Bow Aspiranten 11-12 jaar',  ('IB',), ('AH2', 'AV2'), True),

        ('Longbow klasse 1',                       ('LB',), ('SH', 'SV')),
        ('Longbow klasse 2',                       ('LB',), ('SH', 'SV')),
        ('Longbow Jeugd klasse 1',                 ('LB',), ('JH', 'JV', 'CH', 'CV')),
        ('Longbow Aspiranten < 11 jaar',           ('LB',), ('AH1', 'AV1'), True),
        ('Longbow Aspiranten 11-12 jaar',          ('LB',), ('AH2', 'AV2'), True),
    )

    for tup in WKL_INDIV:
        # neem een eventuele wedstrijdklasse met dezelfde beschrijving buiten gebruik
        neem_wedstrijdklasse_buiten_gebruik(apps, tup[0])

        # maak de nieuwe wedstrijdklasse aan
        create_wedstrijdklasse_individueel(apps, *tup)
    # for



class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0005_wedstrijdklasse_buiten_gebruik'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(wijzig_wedstrijdklassen_hout_jeugd),
    ]


# end of file
