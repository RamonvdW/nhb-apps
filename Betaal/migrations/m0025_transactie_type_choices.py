# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0024_transactie_type'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='betaaltransactie',
            name='transactie_type',
            field=models.CharField(choices=[('HA', 'Handmatig'), ('MP', 'Mollie Payment'), ('MR', 'Mollie Restitutie')],
                                   default='HA', max_length=2),
        ),
    ]

# end of file
