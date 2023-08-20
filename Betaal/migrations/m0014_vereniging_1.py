# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def add_vereniging_new(apps, _):
    """ migratie van veld vereniging """

    ver_klas = apps.get_model('Vereniging', 'Vereniging')
    fix_klas = apps.get_model('Betaal', 'BetaalInstellingenVereniging')

    # maak een cache
    ver_nr2ver = dict()     # [ver_nr] = Vereniging()
    for ver in ver_klas.objects.all():
        ver_nr2ver[ver.ver_nr] = ver
    # for

    for obj in fix_klas.objects.select_related('vereniging').all():
        obj.vereniging_new = ver_nr2ver[obj.vereniging.ver_nr]
        obj.save(update_fields=['vereniging_new'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0002_vereniging_1'),
        ('Betaal', 'm0013_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='betaalinstellingenvereniging',
            name='vereniging_new',
            field=models.OneToOneField(null=True, on_delete=models.deletion.CASCADE, to='Vereniging.vereniging'),
        ),
        migrations.RunPython(add_vereniging_new, migrations.RunPython.noop),
    ]

# end of file
