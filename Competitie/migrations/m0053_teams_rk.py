# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0052_teams_rk'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='kampioenschapteam',
            name='schutters',
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='feitelijke_schutters',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_feitelijke_schutters', to='Competitie.KampioenschapSchutterBoog'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='gekoppelde_schutters',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_gekoppelde_schutters', to='Competitie.KampioenschapSchutterBoog'),
        ),
        migrations.AddField(
            model_name='kampioenschapteam',
            name='tijdelijke_schutters',
            field=models.ManyToManyField(blank=True, related_name='kampioenschapteam_tijdelijke_schutters', to='Competitie.RegioCompetitieSchutterBoog'),
        ),
    ]

# end of file
