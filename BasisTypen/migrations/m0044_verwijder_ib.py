# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def verwijder_buiten_gebruik_en_ib(apps, _):
    """ Verwijder objecten met buiten_gebruik=True:

        Verwijder KalenderWedstrijdKlasse (buiten_gebruik=True)
        Verwijder TemplateCompetitieIndivKlasse (buiten_gebruikt=True)
        Verwijder TemplateCompetitieTeamKlasse (buiten_gebruik=True)
        Verwijder team typen R, BB, IB (buiten_gebruik=True)
        Verwijder boog type IB
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    templatecompetitieindivklasse_klas = apps.get_model('BasisTypen', 'TemplateCompetitieIndivKlasse')
    templatecompetitieteamklasse_klas = apps.get_model('BasisTypen', 'TemplateCompetitieTeamKlasse')
    teamtype_klas = apps.get_model('BasisTypen', 'TeamType')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    for klas in (kalenderwedstrijdklasse_klas,
                 templatecompetitieindivklasse_klas,
                 templatecompetitieteamklasse_klas,
                 teamtype_klas,
                 boogtype_klas):

        objs = klas.objects.filter(buiten_gebruik=True)
        if objs.count() > 0:            # pragma: no cover
            objs.delete()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0043_jongens')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(verwijder_buiten_gebruik_en_ib),
    ]

# end of file
