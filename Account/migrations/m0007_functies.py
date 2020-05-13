# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0002_functies-2019'),
        ('Account', 'm0006_remove_schutterboog'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='account',
            name='functies',
            field=models.ManyToManyField(to='Functie.Functie'),
        ),
    ]

# end of file
