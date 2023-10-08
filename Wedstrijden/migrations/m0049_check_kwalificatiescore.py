# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0048_fix_auto_now'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kwalificatiescore',
            name='check_status',
            field=models.CharField(choices=[('A', 'Afgekeurd'), ('N', 'Nog doen'), ('G', 'Goed')], default='N', max_length=1),
        ),
    ]

# end of file
