# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0013_migratie_1'),
        ('Wedstrijden', 'm0026_migratie_3'),
        ('Bestel', 'm0011_migratie_1')
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='boogtypen',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='deeluitslagen',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='organiserende_vereniging',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='sessies',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijd',
            name='wedstrijdklassen',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdkortingscode',
            name='combi_basis_wedstrijd',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdkortingscode',
            name='uitgegeven_door',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdkortingscode',
            name='voor_sporter',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdkortingscode',
            name='voor_vereniging',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdkortingscode',
            name='voor_wedstrijden',
        ),
        migrations.RemoveField(
            model_name='kalenderwedstrijdsessie',
            name='wedstrijdklassen',
        ),
        migrations.DeleteModel(
            name='KalenderInschrijving',
        ),
        migrations.DeleteModel(
            name='KalenderWedstrijd',
        ),
        migrations.DeleteModel(
            name='KalenderWedstrijdDeeluitslag',
        ),
        migrations.DeleteModel(
            name='KalenderWedstrijdKortingscode',
        ),
        migrations.DeleteModel(
            name='KalenderWedstrijdSessie',
        ),
    ]

# end of file
