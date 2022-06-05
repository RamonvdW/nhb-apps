# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0025_kvk_website_phone'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhbvereniging',
            name='adres_regel1',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='nhbvereniging',
            name='adres_regel2',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='nhbvereniging',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]

# end of file
