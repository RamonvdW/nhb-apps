# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0005_migrate_account_relation'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='functie',
            name='bevestigde_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='functie',
            name='nieuwe_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]

# end of file
