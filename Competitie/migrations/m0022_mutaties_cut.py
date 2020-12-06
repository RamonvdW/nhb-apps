# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0021_deelname'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kampioenschapmutatie',
            name='cut_nieuw',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapmutatie',
            name='cut_oud',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='kampioenschapmutatie',
            name='deelcompetitie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.DeelCompetitie'),
        ),
        migrations.AddField(
            model_name='kampioenschapmutatie',
            name='klasse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.CompetitieKlasse'),
        ),
        migrations.AlterField(
            model_name='kampioenschapmutatie',
            name='deelnemer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Competitie.KampioenschapSchutterBoog'),
        ),
    ]

# end of file
