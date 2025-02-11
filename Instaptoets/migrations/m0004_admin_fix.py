# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Instaptoets', 'm0003_opruimen'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='instaptoets',
            name='huidige_vraag',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='toets_huidige', to='Instaptoets.toetsantwoord'),
        ),
    ]

# end of file
