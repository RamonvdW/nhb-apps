# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BasisTypen', 'm0002_basistypen_2018'),
        ('Account', 'm0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heeft_interesse', models.BooleanField(default=False)),
                ('voor_wedstrijd', models.BooleanField(default=False)),
                ('voorkeur_dutchtarget_18m', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.BoogType')),
            ],
        ),
    ]

# end of file
