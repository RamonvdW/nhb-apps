# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Functie', 'm0006_email'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='functie',
            name='accounts',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]

# end of file
