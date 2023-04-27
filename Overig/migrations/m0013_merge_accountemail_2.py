# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Overig', 'm0012_merge_accountemail_1'),
        ('Account', 'm0024_merge_accountemail_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='sitetijdelijkeurl',
            name='hoortbij_accountemail',
        ),
    ]

# end of file
