# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Scheidsrechter', 'm0006_notificaties'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='scheidsbeschikbaarheid',
            name='opmerking',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='scheidsbeschikbaarheid',
            name='log',
            field=models.TextField(blank=True, default=''),
        ),
    ]

# end of file
