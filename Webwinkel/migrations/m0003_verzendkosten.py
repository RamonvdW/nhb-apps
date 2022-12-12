# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Webwinkel', 'm0002_keuze'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='webwinkelproduct',
            name='type_verzendkosten',
            field=models.CharField(choices=[('pak', 'Pakketpost'), ('brief', 'Briefpost')], default='pak', max_length=5),
        ),
    ]

# end of file
