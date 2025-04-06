# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Webwinkel', 'm0010_bestelling'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='webwinkelkeuze',
            name='ontvangen_euro',
        ),
        migrations.RemoveField(
            model_name='webwinkelkeuze',
            name='totaal_euro',
        ),
        migrations.RemoveField(
            model_name='webwinkelkeuze',
            name='koper',
        ),
    ]

# end of file
