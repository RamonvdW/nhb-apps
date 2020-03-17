# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_regios_2019(rayon_klas, regio_klas):
    """ Deze functie maak de regios aan
        Wordt ook gebruikt vanuit NhbStructuur/tests.py
    """
    # standard regio's in 2019-12-15:
    # rayon 100 voor administratieve verenigingen, zoals het bondsbureau
    regio = regio_klas()
    regio.regio_nr = 100    # ook PK
    regio.rayon = rayon_klas.objects.get(rayon_nr=1)
    regio.naam = "Regio %s" % regio.regio_nr
    regio.save()


def init_regios_2019(apps, schema_editor):
    """ Wijziging regios 2019 """

    # haal de klassen op die van toepassing zijn vóór de migratie
    regio_klas = apps.get_model('NhbStructuur', 'NhbRegio')
    rayon_klas = apps.get_model('NhbStructuur', 'NhbRayon')
    maak_regios_2019(rayon_klas, regio_klas)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0002_nhbstructuur_2018'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='nhbregio',
            name='naam',
            field=models.CharField(max_length=50)),

        migrations.RunPython(init_regios_2019)
    ]

# end of file
