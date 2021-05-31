# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_leeftijdsklasse_volgorde(apps, _):
    """ Geef de twee aspiranten leeftijdsklassen aparte nummers """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    # huidige: 10 = AH1/AV1 Aspiranten tot en met 11 jaar
    #          10 = AH2/AV2 Aspiranten tot en met 13 jaar   --> aanpassen naar 15

    for lkl in leeftijdsklasse_klas.objects.filter(afkorting__in=('AH2', 'AV2')):
        lkl.volgorde = 15
        lkl.save(update_fields=['volgorde'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0018_correct_kalenderwedstrijdklassen'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(zet_leeftijdsklasse_volgorde)
    ]

# end of file
