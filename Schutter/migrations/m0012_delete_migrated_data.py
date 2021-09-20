# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def delete_migrated_data(apps, _):

    # SchutterBoog is gemigreerd naar SporterBoog
    # SchutterVoorkeuren zijn SporterVoorkeuren geworden

    # verwijder nu de oude data
    old_klas = apps.get_model('Schutter', 'SchutterVoorkeuren')
    old_klas.objects.all().delete()

    old_klas = apps.get_model('Schutter', 'SchutterBoog')
    old_klas.objects.all().delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0011_voorkeur_eigen_blazoen'),
        ('Sporter', 'm0002_copy_data'),
        ('Competitie', 'm0054_sporterboog'),
        ('Kalender', 'm0005_sporterboog'),
        ('Score', 'm0010_sporterboog')
    ]

    # migratie functies
    operations = [
        migrations.RunPython(delete_migrated_data)
    ]


# end of file
