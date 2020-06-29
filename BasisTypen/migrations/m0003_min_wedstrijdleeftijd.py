# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

AFK_TO_MIN_LEEFTIJD = {'AH1': 1, 'AV1': 1,  # aspiranten 1: 11-
                       'AH2': 12, 'AV2': 12,  # aspiranten 2: 12..13
                       'CH': 14, 'CV': 14,  # cadetten: 14..17
                       'JH': 18, 'JV': 18,  # junioren: 18..20
                       'SH': 21, 'SV': 21}  # senioren: 21+


def update_leeftijdsklassen_2018(apps, _):
    """ AddField heeft default alle min_wedstrijdleeftijd op 0 gezet
        Deze functie zetten we juiste waarden
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    for obj in klas.objects.all():
        obj.min_wedstrijdleeftijd = AFK_TO_MIN_LEEFTIJD[obj.afkorting]
        obj.save()
    # for


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0002_basistypen_2018'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='leeftijdsklasse',
            name='min_wedstrijdleeftijd',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(update_leeftijdsklassen_2018),
    ]

# end of file
