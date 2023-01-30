# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0033_cleanup'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='verkoopvoorwaarden_status_acceptatie',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='verkoopvoorwaarden_status_when',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='verkoopvoorwaarden_status_who',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='voorwaarden_a_status_when',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

# end of file
