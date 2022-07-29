# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.migrations.m0042_squashed import INDIV_COMP_KLASSEN, KALENDERWEDSTRIJDENKLASSEN


def update_kalender_klassen(apps, _):
    """ Voeg een afkorting toe aan de WA / NHB klassen en werk de beschrijving bij
        (heren/vrouwen --> heren/dames + verwijderen oude WA naam)
    """

    volgorde2new = dict()
    for volgorde, _, _, afkorting, beschrijving in KALENDERWEDSTRIJDENKLASSEN:
        tup = (afkorting, beschrijving)
        volgorde2new[volgorde] = tup
    # for

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')

    for obj in kalenderwedstrijdklasse_klas.objects.filter(afkorting='?'):
        obj.afkorting, obj.beschrijving = volgorde2new[obj.volgorde]
        obj.save(update_fields=['afkorting', 'beschrijving'])
    # for


def update_competitie_klassen(apps, _):
    """ Voeg een afkorting toe aan de WA / NHB klassen en werk de beschrijving bij
        (heren/vrouwen --> heren/dames + verwijderen oude WA naam)
    """

    volgorde2new = dict()
    for tup in INDIV_COMP_KLASSEN:
        volgorde, beschrijving = tup[0:0+2]
        volgorde2new[volgorde] = beschrijving
    # for

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    competitie_indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')

    for obj in competitie_indiv_klas.objects.all():
        obj.beschrijving = volgorde2new[obj.volgorde]
        obj.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0044_verwijder_ib')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(update_kalender_klassen),
        migrations.RunPython(update_competitie_klassen)
    ]

# end of file
