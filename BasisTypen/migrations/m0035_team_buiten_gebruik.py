# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_buiten_gebruik_ib(apps, _):
    """ Zet team typen met het IB boogtype op 'buiten gebruik'
    """

    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    if boogtype_klas.objects.filter(afkorting='IB').count() > 0:            # pragma: no cover

        ib_boog = boogtype_klas.objects.get(afkorting='IB')

        for teamtype in ib_boog.teamtype_set.all():
            teamtype.buiten_gebruik = True
            teamtype.save(update_fields=['buiten_gebruik'])
        # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0034_ifaa_bogen'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='teamtype',
            name='buiten_gebruik',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(zet_buiten_gebruik_ib),
    ]

# end of file
