# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Opleidingen', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='opleidingdeelnemer',
            name='wanneer_aangemeld',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='opleidingmoment',
            name='opleider_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]

# end of file
