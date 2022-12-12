# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Webwinkel', 'm0003_verzendkosten'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='webwinkelkeuze',
            name='status',
            field=models.CharField(choices=[('M', 'Reservering'), ('B', 'Besteld'), ('BO', 'Betaald'), ('A', 'Geannuleerd')], default='M', max_length=2),
        ),
    ]

# end of file
