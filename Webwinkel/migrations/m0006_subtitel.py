# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Webwinkel', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='webwinkelproduct',
            name='sectie_subtitel',
            field=models.CharField(blank=True, default='', max_length=250),
        ),
    ]

# end of file
