# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_rayon_nr(apps, _):

    regio_klas = apps.get_model('NhbStructuur', 'Regio')

    for regio in regio_klas.objects.select_related('rayon').all():
        regio.rayon_nr = regio.rayon.rayon_nr
        regio.save(update_fields=['rayon_nr'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0036_renames'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regio',
            name='rayon_nr',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(zet_rayon_nr, migrations.RunPython.noop),
    ]

# end of file
