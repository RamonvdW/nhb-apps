# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='evenementinschrijving',
            old_name='ontvangen_euro',
            new_name='bedrag_ontvangen',
        ),
        migrations.RenameField(
            model_name='evenementafgemeld',
            old_name='ontvangen_euro',
            new_name='bedrag_ontvangen',
        ),
        migrations.RenameField(
            model_name='evenementafgemeld',
            old_name='retour_euro',
            new_name='bedrag_retour',
        ),
        migrations.RemoveField(
            model_name='evenementinschrijving',
            name='retour_euro',
        ),
    ]

# end of file
