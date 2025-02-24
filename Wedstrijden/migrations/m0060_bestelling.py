# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # migratie functies
    dependencies = [
        ('Bestelling', 'm0005_regel'),
        ('Wedstrijden', 'm0059_langere_titel'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdinschrijving',
            name='bestelling',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Bestelling.bestellingregel'),
        ),
    ]

# end of file
