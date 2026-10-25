# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Scheidsrechter', 'm0013_mutatie_door_langer'),
        ('Sporter', 'm0034_sr0'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijddagscheidsrechters',
            name='gekozen_srio1',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='gekozen_srio1', to='Sporter.sporter'),
        ),
        migrations.AddField(
            model_name='wedstrijddagscheidsrechters',
            name='gekozen_srio2',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='gekozen_srio2', to='Sporter.sporter'),
        ),
        migrations.AddField(
            model_name='wedstrijddagscheidsrechters',
            name='gekozen_srio3',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='gekozen_srio3', to='Sporter.sporter'),
        ),
        migrations.AddField(
            model_name='matchscheidsrechters',
            name='gekozen_srio1',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='match_gekozen_srio1', to='Sporter.sporter'),
        ),
        migrations.AddField(
            model_name='matchscheidsrechters',
            name='gekozen_srio2',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='match_gekozen_srio2', to='Sporter.sporter'),
        ),
    ]

# end of file
