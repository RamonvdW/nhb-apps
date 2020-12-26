# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def markeer_onbekend_niet_rk_bk(apps, _):
    """ Boog typen jaar 2018, volgens spec v1.2, tabel 2.2 """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    indiv_wedstrijdklasse_klas = apps.get_model('BasisTypen', 'IndivWedstrijdklasse')

    for obj in indiv_wedstrijdklasse_klas.objects.filter(is_onbekend=True):
        obj.niet_voor_rk_bk = True
        obj.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0010_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(markeer_onbekend_niet_rk_bk),
    ]

# end of file
