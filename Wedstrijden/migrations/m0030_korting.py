# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0029_klasse_log'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='wedstrijdinschrijving',
            old_name='gebruikte_code',
            new_name='korting',
        ),
        migrations.RemoveField(
            model_name='wedstrijdkortingscode',
            name='code',
        ),
        migrations.RemoveField(
            model_name='wedstrijdkortingscode',
            name='combi_basis_wedstrijd',
        ),
        migrations.RenameModel(
            old_name='WedstrijdKortingscode',
            new_name='WedstrijdKorting',
        ),
        migrations.AlterModelOptions(
            name='wedstrijdkorting',
            options={'verbose_name': 'Wedstrijd korting', 'verbose_name_plural': 'Wedstrijd kortingen'},
        ),
    ]

# end of file
