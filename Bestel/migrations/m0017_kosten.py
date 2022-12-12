# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0016_webwinkel'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_euro_cat1',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_euro_cat2',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_euro_cat3',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_percentage_cat1',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_percentage_cat2',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='btw_percentage_cat3',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelmandje',
            name='verzendkosten_euro',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_euro_cat1',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_euro_cat2',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_euro_cat3',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_percentage_cat1',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_percentage_cat2',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='btw_percentage_cat3',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AddField(
            model_name='bestelling',
            name='verzendkosten_euro',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=6),
        ),
    ]

# end of file
