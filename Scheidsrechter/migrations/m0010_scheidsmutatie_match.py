# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0113_squashed'),
        ('Scheidsrechter', 'm0009_wedstrijd_optional'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='scheidsmutatie',
            name='match',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    to='Competitie.competitiematch'),
        ),
    ]

# end of file
