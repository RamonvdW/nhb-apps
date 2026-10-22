# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0033_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='sporter',
            name='scheids',
            field=models.CharField(blank=True, default='N', max_length=2,
                                   choices=[('N', 'Niet'),
                                            ('B', 'Bondsscheidsrechter'),
                                            ('V', 'Verenigingsscheidsrechter'),
                                            ('I', 'Internationaal Scheidsrechter'),
                                            ('O', 'Scheidsrechter in opleiding')]),
        ),
    ]

# end of file
