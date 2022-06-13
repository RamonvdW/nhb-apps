# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations
from BasisTypen.models import ORGANISATIE_NHB


def corrigeer_kalender_klasse_140(apps, _):
    """ Corrigeer KalenderWedstrijdklasse 140

        (140, 'R', 'CH', 'Recurve Onder 18 (cadet)'),

        CH moet zijn CA
    """

    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    kal = kalenderwedstrijdklasse_klas.objects.select_related('leeftijdsklasse').get(volgorde=140)

    if kal.leeftijdsklasse.afkorting == 'CH':           # pragma: no cover

        lkl = leeftijdsklasse_klas.objects.get(afkorting='CA')
        kal.leeftijdsklasse = lkl
        kal.organisatie = ORGANISATIE_NHB
        kal.save(update_fields=['leeftijdsklasse', 'organisatie'])


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0035_team_buiten_gebruik'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(corrigeer_kalender_klasse_140),
    ]

# end of file
