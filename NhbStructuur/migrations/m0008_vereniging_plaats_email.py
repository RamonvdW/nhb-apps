# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0007_secretaris_set-null'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhbvereniging',
            name='plaats',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='nhbvereniging',
            name='contact_email',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]

# end of file
