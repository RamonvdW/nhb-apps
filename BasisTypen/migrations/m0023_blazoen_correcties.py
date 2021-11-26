# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import BLAZOEN_DT


def blazoenen_aanpassen(apps, _):
    """ Kleine corrected in de blazoenen:

        RK/BK teams: Recurve ERE moet "alleen DT" zijn (was: "40cm of DT").

        Regio teamcompetitie: alle Recurve team klassen moeten "40cm of DT" zijn (was: alleen 40cm)
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    team_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'TeamWedstrijdklasse')

    # zie m0022_squashed voor volgorde
    for klasse in team_wedstrijdklasse_klas.objects.filter(volgorde__in=(10, 11, 12, 13, 14)):

        if klasse.volgorde == 10:
            # Recurve ERE mag alleen op DT tijdens de RK/BK
            klasse.blazoen1_18m_rk_bk = BLAZOEN_DT      # 40cm,DT --> DT,DT
            klasse.save(update_fields=['blazoen1_18m_rk_bk'])
        else:
            # recurve teams mogen tijdens de regiocompetitie kiezen uit DT of 40cm
            klasse.blazoen2_18m_regio = BLAZOEN_DT      # 40cm,40cm --> 40cm,DT
            klasse.save(update_fields=['blazoen2_18m_regio'])
    # for


class Migration(migrations.Migration):

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0022_squashed'),
    ]

    operations = [
        migrations.RunPython(blazoenen_aanpassen),
    ]

# end of file
