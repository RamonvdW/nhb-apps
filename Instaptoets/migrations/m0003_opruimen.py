# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Instaptoets', 'm0002_categorie'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='toetsantwoord',
            options={'verbose_name': 'Toets antwoord', 'verbose_name_plural': 'Toets antwoorden'},
        ),
        migrations.DeleteModel(
            name='VoorstelVraag',
        ),
    ]

# end of file
