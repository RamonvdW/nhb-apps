# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Scheidsrechter', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijddagscheids',
            name='is_hoofd_sr',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scheidsbeschikbaarheid',
            name='wedstrijd',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd'),
        ),
    ]

# end of file
