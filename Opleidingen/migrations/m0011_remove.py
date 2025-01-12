# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleidingen', 'm0010_prep_migrate'),
        ('Opleiding', 'm0001_diploma'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opleidingdeelnemer',
            name='koper',
        ),
        migrations.RemoveField(
            model_name='opleidingdeelnemer',
            name='sporter',
        ),
        migrations.RemoveField(
            model_name='opleidingdiploma',
            name='sporter',
        ),
        migrations.RemoveField(
            model_name='opleidingmoment',
            name='locatie',
        ),
        migrations.DeleteModel(
            name='Opleiding',
        ),
        migrations.DeleteModel(
            name='OpleidingDeelnemer',
        ),
        migrations.DeleteModel(
            name='OpleidingDiploma',
        ),
        migrations.DeleteModel(
            name='OpleidingMoment',
        ),
    ]

# end of file
