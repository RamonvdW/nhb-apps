# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Functie', 'm0002_functies-2019'),
        ('Competitie', 'm0003_delete_favoriete-bestuurders'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='deelcompetitie',
            name='functies',
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='functie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Functie.Functie'),
        ),
    ]

# end of file
