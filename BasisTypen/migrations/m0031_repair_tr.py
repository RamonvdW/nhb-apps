# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def repair_tr(apps, _):
    """ corrigeer de Traditional kalender wedstrijdklassen: boogtypen IB --> TR
        komt alleen voor bij upgrade
    """

    # alle bestaande bogen zijn World Archery en dat is ook de default, dus niets aan te passen
    kalender_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    tr_boog = boogtype_klas.objects.get(afkorting='TR')

    # TR klassen hebben volgnummers blok 500
    for kal in (kalender_klas
                .objects
                .filter(volgorde__range=(500, 599),
                        boogtype__afkorting='IB')):         # pragma: no cover
        kal.boogtype = tr_boog
        kal.save(update_fields=['boogtype'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0030_organisatie'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(repair_tr),
    ]

# end of file
