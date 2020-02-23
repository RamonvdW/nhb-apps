# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


RAYONS_2018 = (
    (1, "Rayon 1", "Noord Nederland"),
    (2, "Rayon 2", "Zuid-West Nederland"),
    (3, "Rayon 3", "Oost Brabant en Noord Limburg"),
    (4, "Rayon 4", "Zuid- en Midden-Limburg")
)


def maak_rayons_2018(rayon_klas):
    """ Deze functie maakt de rayons aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    rayon = rayon_klas()
    for nummer, naam, geo in RAYONS_2018:
        rayon.rayon_nr = nummer     # ook PK
        rayon.naam = naam
        rayon.geografisch_gebied = geo
        rayon.save()
    # for


def init_rayons_2018(apps, schema_editor):
    """ Standaard rayons 2018 """

    # haal de klassen op die van toepassing zijn vóór de migratie
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    maak_rayons_2018(rayon_klas)


def maak_regios_2018(rayon_klas, regio_klas):
    """ Deze functie maak de regios aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    # standard regio's in 2019-07-20:
    # elk rayon heeft 4 regios --> totaal 16 regios
    # 101 = rayon 1, eerst regio
    # 116 = rayon 4, laatste regio
    regio = regio_klas()
    regio.regio_nr = 101    # eerste regio nummer (ook PK)
    for rayon_nr in (1, 2, 3, 4):
        # haal de rayon referentie op
        regio.rayon = rayon_klas.objects.get(rayon_nr=rayon_nr)

        # 4 regios per rayon
        for _ in (1, 2, 3, 4):
            regio.naam = "Regio %s" % regio.regio_nr
            regio.save()

            regio.regio_nr += 1     # nieuwe PK
        # for
    # for


def init_regios_2018(apps, schema_editor):
    """ Standard regios 2018 """

    # haal de klassen op die van toepassing zijn vóór de migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    maak_regios_2018(rayon_klas, regio_klas)


class Migration(migrations.Migration):
    """ Migratie classs voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_rayons_2018),
        migrations.RunPython(init_regios_2018),
    ]

# end of file
