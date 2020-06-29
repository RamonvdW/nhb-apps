# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def hernoem_cwz_hwl(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    # hernoem alle CWZ functies naar HWL
    # behoud de gebruikers die eraan gekoppeld zijn
    for obj in functie_klas.objects.filter(rol='CWZ'):                   # pragma: no cover
        obj.rol = 'HWL'
        # let op: in sync houden met management command import_nhb_crm
        obj.beschrijving = "Hoofdwedstrijdleider %s" % obj.nhb_ver.nhb_nr
        obj.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0011_clusters'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(hernoem_cwz_hwl),
    ]

# end of file
