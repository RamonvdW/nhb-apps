# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def corrigeer_volgorde(apps, _):
    """ de volgorde van de kalenderwedstrijdklassen IB en LB moet andersom """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    boog_ib = boogtype_klas.objects.get(afkorting='IB')
    boog_lb = boogtype_klas.objects.get(afkorting='LB')

    # pas de volgorde aan: IB +100, LB -100
    for obj in leeftijdsklasse_klas.objects.filter(boogtype__afkorting__in=('IB', 'LB')):       # pragma: no cover
        old = obj.volgorde
        if obj.volgorde >= 500:
            # IB beschrijving
            obj.volgorde -= 100
            obj.boogtype = boog_ib
        else:
            # LB
            obj.volgorde += 100
            obj.boogtype = boog_lb

        obj.save(update_fields=['volgorde', 'boogtype'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0017_master_wa'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(corrigeer_volgorde),
    ]

# end of file
