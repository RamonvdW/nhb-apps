# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0020_squashed'),
        ('Score', 'm0015_uitslag_1'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitiewedstrijduitslag',
            name='nieuwe_uitslag',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Score.uitslag'),
        ),
    ]

# end of file
