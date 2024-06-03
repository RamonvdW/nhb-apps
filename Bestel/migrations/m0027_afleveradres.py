# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0026_verkoper_btw_nr'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelling',
            name='afleveradres_regel_1',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='afleveradres_regel_2',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='afleveradres_regel_3',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='afleveradres_regel_4',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='afleveradres_regel_5',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='afleveradres_regel_1',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='afleveradres_regel_2',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='afleveradres_regel_3',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='afleveradres_regel_4',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='afleveradres_regel_5',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
    ]

# end of file
