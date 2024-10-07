# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0054_url_uitslag'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='wedstrijd',
            old_name='url_uitslag',
            new_name='url_uitslag_1',
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='url_uitslag_2',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='url_uitslag_3',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='url_uitslag_4',
            field=models.CharField(default='', max_length=128),
        ),
    ]

# end of file
