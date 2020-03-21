# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    initial = True
    dependencies = [
        ('Account', 'm0006_remove_schutterboog'),
        ('BasisTypen', 'm0006_hout-klassen-jeugd'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heeft_interesse', models.BooleanField(default=True)),
                ('voor_wedstrijd', models.BooleanField(default=False)),
                ('voorkeur_dutchtarget_18m', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BasisTypen.BoogType')),
            ],
        ),
    ]

# end of file
