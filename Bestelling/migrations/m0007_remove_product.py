# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0006_prod2regel'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='bestelling',
            name='producten',
        ),
        migrations.RemoveField(
            model_name='bestellingmandje',
            name='producten',
        ),
        migrations.RemoveField(
            model_name='bestellingmutatie',
            name='product',
        ),
        migrations.DeleteModel(
            name='BestellingProduct',
        ),
    ]

# end of file
