# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('CompLaagBond', 'm0001_initial'),
        ('CompLaagRayon', 'm0001_initial'),
        ('Competitie', 'm0121_team_result_shootoff'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='competitiemutatie',
            name='deelnemer',
        ),
        migrations.RemoveField(
            model_name='competitiemutatie',
            name='kampioenschap',
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='deelnemer_bk',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=models.deletion.CASCADE, to='CompLaagBond.deelnemerbk'),
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='deelnemer_rk',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=models.deletion.CASCADE, to='CompLaagRayon.deelnemerrk'),
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='kamp_bk',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=models.deletion.CASCADE, to='CompLaagBond.kampbk'),
        ),
        migrations.AddField(
            model_name='competitiemutatie',
            name='kamp_rk',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=models.deletion.CASCADE, to='CompLaagRayon.kamprk'),
        ),
    ]

# end of file