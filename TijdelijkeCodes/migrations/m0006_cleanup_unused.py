# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('TijdelijkeCodes', 'm0005_scheids_beschikbaarheid'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='tijdelijkecode',
            name='hoort_bij_sporter',
        ),
        migrations.RemoveField(
            model_name='tijdelijkecode',
            name='hoort_bij_wedstrijd',
        ),
    ]

# end of file
