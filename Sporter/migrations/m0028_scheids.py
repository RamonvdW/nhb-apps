# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0027_vereniging_2'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sporter',
            name='scheids',
            field=models.CharField(blank=True,
                                   choices=[('N', 'Niet'),
                                            ('B', 'Bondsscheidsrechter'),
                                            ('V', 'Verenigingsscheidsrechter'),
                                            ('I', 'Internationaal Scheidsrechter')],
                                   default='N',
                                   max_length=2),
        ),
    ]

# end of file