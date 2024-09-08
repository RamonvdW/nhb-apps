# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Spelden', 'm0004_defaults'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='speldaanvraag',
            name='last_email_reminder',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

# end of file
