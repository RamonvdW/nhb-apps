# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Instaptoets', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Categorie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(blank=True, default='', max_length=100)),
            ],
            options={
                'verbose_name': 'Categorie',
                'verbose_name_plural': 'Categorieën',
            },
        ),
        migrations.AddField(
            model_name='vraag',
            name='categorie',
            field=models.ForeignKey(on_delete=models.deletion.SET_NULL, blank=True, null=True,
                                    to='Instaptoets.categorie'),
        ),
    ]

# end of file
