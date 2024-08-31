# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Webwinkel', 'm0007_kleding_maat'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='webwinkelproduct',
            name='gewicht_gram',
            field=models.SmallIntegerField(default=0),
        ),
    ]

# end of file
