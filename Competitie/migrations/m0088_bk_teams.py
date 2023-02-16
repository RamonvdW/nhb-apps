# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0087_team_volgorde'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapteam',
            name='rank',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='rk_kampioen_label',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='volgorde',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='deelname',
            field=models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?',
                                   max_length=1),
        ),
    ]

# end of file
