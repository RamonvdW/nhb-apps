# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import migrations, models


def verwijder_alle_taken(apps, _):
    """ Verwijder alle taken, omdat toegekend_aan[_account] vervalt en taken dus 'zwevend' worden
    """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    taak_klas = apps.get_model('Taken', 'Taak')
    taak_klas.objects.all().delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0013_telefoon_en_rol_mo'),
        ('Taken', 'm0003_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='taak',
            name='toegekend_aan',
        ),
        migrations.RemoveField(
            model_name='taak',
            name='handleiding_pagina',
        ),
        migrations.RemoveField(
            model_name='taak',
            name='deelcompetitie',
        ),
        migrations.AddField(
            model_name='taak',
            name='toegekend_aan_functie',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='functie_taken', to='Functie.functie'),
        ),
        migrations.AlterField(
            model_name='taak',
            name='beschrijving',
            field=models.TextField(max_length=5000),
        ),
        migrations.AlterField(
            model_name='taak',
            name='log',
            field=models.TextField(blank=True, max_length=5000),
        ),
        migrations.RunPython(verwijder_alle_taken, migrations.RunPython.noop)
    ]

# end of file
