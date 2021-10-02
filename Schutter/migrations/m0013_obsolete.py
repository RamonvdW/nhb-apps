# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    # volgorde afdwingen
    dependencies = [
        ('Schutter', 'm0012_delete_migrated_data'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='schuttervoorkeuren',
            name='nhblid',
        ),
        migrations.DeleteModel(
            name='SchutterBoog',
        ),
        migrations.DeleteModel(
            name='SchutterVoorkeuren',
        ),
    ]

# end of file
