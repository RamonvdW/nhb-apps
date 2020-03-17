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
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Competitie', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='FavorieteBestuurders',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('favoriet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='favorietebestuurder', to=settings.AUTH_USER_MODEL)),
                ('zelf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Favoriete bestuurders',
                'verbose_name_plural': 'Favoriete bestuurders',
            },
        ),
    ]

# end of file
