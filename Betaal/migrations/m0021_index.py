# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0020_refunds'),
    ]

    # migratie functies
    operations = [
        migrations.AddIndex(
            model_name='betaaltransactie',
            index=models.Index(fields=['payment_id'], name='Betaal_beta_payment_683df1_idx'),
        ),
    ]

# end of file
