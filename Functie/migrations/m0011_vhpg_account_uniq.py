# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Functie', 'm0010_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='verklaringhanterenpersoonsgegevens',
            name='account',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vhpg', to=settings.AUTH_USER_MODEL),
        ),
    ]

# end of file
