# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Overig', 'm0009_squashed'),
        ('Feedback', 'm0001_migrate'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='SiteFeedback',
        ),
    ]

# end of file
