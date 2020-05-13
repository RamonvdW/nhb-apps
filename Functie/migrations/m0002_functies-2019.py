# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def maak_functie(functie_klas, beschrijving, rol, comp_type):

    functie = functie_klas()
    functie.beschrijving = beschrijving
    functie.rol = rol
    functie.comp_type = comp_type
    functie.save()

    return functie


def init_functies_2019(apps, schema_editor):
    """ Functies voor de NHB structuur van 2019 """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    functie_klas = apps.get_model('Functie', 'Functie')

    AFSTAND = [('18', 'Indoor'),
               ('25', '25m 1pijl')]

    ADMINISTRATIEVE_REGIO = 100

    for comp_type, comp_descr in AFSTAND:
        # BKO
        maak_functie(functie_klas, 'BKO ' + comp_descr, 'BKO', comp_type)

        # RKO per rayon
        for obj in rayon_klas.objects.all():
            functie = maak_functie(functie_klas, 'RKO Rayon %s %s' % (obj.rayon_nr, comp_descr), 'RKO', comp_type)
            functie.nhb_rayon = obj
            functie.save()
        # for

        # RCL per regio
        for obj in regio_klas.objects.all():
            if obj.regio_nr != ADMINISTRATIEVE_REGIO:
                functie = maak_functie(functie_klas, 'RCL Regio %s %s' % (obj.regio_nr, comp_descr), 'RCL', comp_type)
                functie.nhb_regio = obj
                functie.save()
        # for
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0001_initial'),
        ('NhbStructuur', 'm0003_nhbstructuur_2019'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(init_functies_2019),
    ]

# end of file
