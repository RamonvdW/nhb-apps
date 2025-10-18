# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def zet_sv_icon(apps, _):
    # haal de klassen op die van toepassing zijn vóór de migratie
    ander_klas = apps.get_model('Records', 'AnderRecord')

    for ander_obj in ander_klas.objects.all():
        ander_obj.sv_icon = 'record ander'
        ander_obj.save(update_fields=['sv_icon'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Records', 'm0015_volgorde'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='anderrecord',
            old_name='icoon',
            new_name='sv_icon',
        ),
        migrations.RunPython(zet_sv_icon)
    ]

# end of file
