# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0015_longer_otp_code'),
        ('Functie', 'm0009_move_vhpg')
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='HanterenPersoonsgegevens',
        ),
    ]

# end of file
