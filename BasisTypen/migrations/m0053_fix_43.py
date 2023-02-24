# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def fix_lkl_43(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    lkl_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    lkl = lkl_klas.objects.get(volgorde=43)
    lkl.klasse_kort = 'Senior'
    lkl.save(update_fields=['klasse_kort'])


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0052_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(fix_lkl_43, migrations.RunPython.noop)
    ]

# end of file
