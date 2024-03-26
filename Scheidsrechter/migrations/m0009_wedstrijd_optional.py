# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0053_verstop'),
        ('Scheidsrechter', 'm0008_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='scheidsmutatie',
            name='wedstrijd',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    to='Wedstrijden.wedstrijd'),
        ),
    ]

# end of file
