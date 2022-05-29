# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_buiten_gebruik_ib(apps, _):
    """ Zet het IB boogtype op 'buiten gebruik'
        Zet de kalenderwedstrijdklassen met boogtype IB op 'buiten gebruik'
    """

    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    if boogtype_klas.objects.filter(afkorting='IB').count() > 0:            # pragma: no cover

        ib_boog = boogtype_klas.objects.get(afkorting='IB')
        ib_boog.buiten_gebruik = True
        ib_boog.save(update_fields=['buiten_gebruik'])

        kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')

        for kal in kalenderwedstrijdklasse_klas.objects.filter(boogtype=ib_boog):
            kal.buiten_gebruik = True
            kal.save(update_fields=['buiten_gebruik'])
        # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0032_organisatie_nhb'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='boogtype',
            name='buiten_gebruik',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_buiten_gebruik_ib),
    ]

# end of file