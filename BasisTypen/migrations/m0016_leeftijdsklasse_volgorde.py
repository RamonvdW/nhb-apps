# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_leeftijdsklasse_volgorde(apps, _):
    """ Zet het nieuwe volgorde veld op LeeftijdsKlasse """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    leeftijdsklasse_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

    volgorde = 10
    for kort in ('Aspirant', 'Cadet', 'Junior', 'Senior', 'Master', 'Veteraan'):
        for lkl in leeftijdsklasse_klas.objects.filter(klasse_kort=kort):
            lkl.volgorde = volgorde
            lkl.save(update_fields=['volgorde'])
        # for

        volgorde += 10
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0015_kalenderwedstrijdklasse'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='leeftijdsklasse',
            name='volgorde',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(zet_leeftijdsklasse_volgorde)
    ]

# end of file
