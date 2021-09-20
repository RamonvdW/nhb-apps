# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def delete_migrated_data(apps, _):

    # NhbLid is gemigreerd naar Sporter.Sporter
    # Speelsterkte is gemigreerd naar Sporter.Speelsterkte

    # verwijder nu de oude data
    old_klas = apps.get_model('NhbStructuur', 'Speelsterkte')
    old_klas.objects.all().delete()

    old_klas = apps.get_model('NhbStructuur', 'NhbLid')
    old_klas.objects.all().delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0021_verwijder_rayon_geografisch_gebied'),
        ('Sporter', 'm0002_copy_data'),
        ('Records', 'm0010_sporter'),
        ('Schutter', 'm0012_delete_migrated_data')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(delete_migrated_data)
    ]


# end of file
