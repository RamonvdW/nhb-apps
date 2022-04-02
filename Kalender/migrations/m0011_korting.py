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
        ('Kalender', 'm0010_inschrijving'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalendermutatie',
            name='korting',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Kalender.kalenderwedstrijdkortingscode'),
        ),
        migrations.AddField(
            model_name='kalendermutatie',
            name='korting_voor_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Account.account'),
        ),
    ]

# end of file
