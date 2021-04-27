# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from Overig.helpers import maak_unaccented


def maak_unaccented_naam(apps, _):
    """ zet het nieuwe veld voor alle NhbLid objecten """

    # haal de klassen op die van toepassing zijn vóór de migratie
    nhblid_klas = apps.get_model('NhbStructuur', 'NhbLid')

    for lid in nhblid_klas.objects.all():  # pragma: no cover
        volledige_naam = lid.voornaam + " " + lid.achternaam
        lid.unaccented_naam = maak_unaccented(volledige_naam)
        lid.save(update_fields=['unaccented_naam'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0017_rename_ver_nhb_nr'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhblid',
            name='unaccented_naam',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.RunPython(maak_unaccented_naam)
    ]

# end of file
