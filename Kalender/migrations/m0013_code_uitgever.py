# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0024_squashed'),
        ('Kalender', 'm0012_rename'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijdkortingscode',
            name='uitgegeven_door',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='korting_uitgever', to='NhbStructuur.nhbvereniging'),
        ),
    ]

# end of file
