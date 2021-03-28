# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0016_lid_tot_einde_jaar'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='nhbvereniging',
            old_name='nhb_nr',
            new_name='ver_nr',
        ),
    ]

# end of file
