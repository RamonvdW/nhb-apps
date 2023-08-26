# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Betaal', 'm0015_vereniging_2'),
        ('Competitie', 'm0103_vereniging_2'),
        ('Functie', 'm0021_vereniging_2'),
        ('NhbStructuur', 'm0034_squashed'),
        ('Sporter', 'm0027_vereniging_2'),
        ('Vereniging', 'm0003_vereniging_2'),
        ('Wedstrijden', 'm0042_vereniging_2'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='NhbVereniging',
        ),
    ]

# end of file
