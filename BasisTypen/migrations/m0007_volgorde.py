# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_volgorde(apps, beschrijving):
    """ sorteervolgorde voor de bekende boogtypen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # zet de volgorde en laat wat ruimte vrij
    boogtype = boogtype_klas.objects.get(afkorting='R')
    boogtype.volgorde = 'A'
    boogtype.save()

    boogtype = boogtype_klas.objects.get(afkorting='C')
    boogtype.volgorde = 'D'
    boogtype.save()

    boogtype = boogtype_klas.objects.get(afkorting='BB')
    boogtype.volgorde = 'I'
    boogtype.save()

    boogtype = boogtype_klas.objects.get(afkorting='IB')
    boogtype.volgorde = 'M'
    boogtype.save()

    boogtype = boogtype_klas.objects.get(afkorting='LB')
    boogtype.volgorde = 'S'
    boogtype.save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0006_hout-klassen-jeugd'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='boogtype',
            name='volgorde',
            field=models.CharField(default='?', max_length=1),
        ),
        migrations.RunPython(zet_volgorde),
    ]

# end of file
