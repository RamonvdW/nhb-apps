# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Registreer', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='gastregistratie',
            name='wa_id',
            field=models.CharField(blank=True, default='', max_length=8),
        ),
        migrations.AddField(
            model_name='gastregistratie',
            name='club_plaats',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.RenameField(
            model_name='gastregistratie',
            old_name='eigen_vereniging',
            new_name='club',
        ),
    ]

# end of file
