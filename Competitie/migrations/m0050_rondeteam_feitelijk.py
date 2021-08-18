# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0049_vsg'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='regiocompetitierondeteam',
            name='schutters',
        ),
        migrations.AddField(
            model_name='regiocompetitierondeteam',
            name='deelnemers_feitelijk',
            field=models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Competitie.RegioCompetitieSchutterBoog'),
        ),
        migrations.AddField(
            model_name='regiocompetitierondeteam',
            name='deelnemers_geselecteerd',
            field=models.ManyToManyField(blank=True, related_name='teamronde_geselecteerd', to='Competitie.RegioCompetitieSchutterBoog'),
        ),
    ]

# end of file
