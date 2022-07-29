# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def update_competitie_klassen(apps, _):
    """ Voeg een afkorting toe aan de WA / NHB klassen en werk de beschrijving bij
        (heren/vrouwen --> heren/dames + verwijderen oude WA naam)
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    template_indiv_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    competitie_indiv_klas = apps.get_model('Competitie', 'CompetitieIndivKlasse')

    volgorde2new = dict()
    for klasse in template_indiv_klas.objects.all():
        volgorde2new[klasse.volgorde] = klasse.beschrijving
    # for

    for obj in competitie_indiv_klas.objects.all():
        obj.beschrijving = volgorde2new[obj.volgorde]
        obj.save(update_fields=['beschrijving'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0045_wkl_afk_beschr'),
        ('Competitie', 'm0075_squashed')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(update_competitie_klassen)
    ]

# end of file
