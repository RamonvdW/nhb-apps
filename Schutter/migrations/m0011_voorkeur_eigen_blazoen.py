# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0010_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='schuttervoorkeuren',
            old_name='voorkeur_dutchtarget_18m',
            new_name='voorkeur_eigen_blazoen',
        ),
    ]

# end of file
