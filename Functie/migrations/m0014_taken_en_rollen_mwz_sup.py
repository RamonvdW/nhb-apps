# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_nieuwe_functies(apps, _):
    """ Nieuwe functies: Site Support en Manager Wedstrijdzaken """

    # haal de klassen op die van toepassing zijn op het moment van migratie
    functie_klas = apps.get_model('Functie', 'Functie')

    functie_klas(rol='MWZ', beschrijving='Manager Wedstrijdzaken').save()
    functie_klas(rol='SUP', beschrijving='Support').save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0013_telefoon_en_rol_mo'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='functie',
            name='laatste_email_over_taken',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='functie',
            name='optout_herinnering_taken',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='functie',
            name='optout_nieuwe_taak',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(maak_nieuwe_functies, reverse_code=migrations.RunPython.noop),
    ]

# end of file
