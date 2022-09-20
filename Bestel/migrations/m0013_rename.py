# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0012_betaal_methode'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='bestelmutatie',
            old_name='kortingscode',
            new_name='korting',
        ),
    ]

# end of file
