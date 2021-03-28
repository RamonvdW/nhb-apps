# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0004_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='histcompetitieindividueel',
            options={'verbose_name': 'Historische individuele competitie', 'verbose_name_plural': 'Historische individuele competitie'},
        ),
        migrations.AlterModelOptions(
            name='histcompetitieteam',
            options={'verbose_name': 'Historische team competitie', 'verbose_name_plural': 'Historische team competitie'},
        ),
    ]

# end of file
