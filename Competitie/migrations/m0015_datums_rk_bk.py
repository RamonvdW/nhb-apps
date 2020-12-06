# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from datetime import date


def initialiseer_nieuwe_datums(apps, _):
    """ zet een datum in de nieuwe velden """
    competitie_klas = apps.get_model('Competitie', 'Competitie')

    for comp in competitie_klas.objects.all():      # pragma: no cover
        begin_rk = date(year=comp.begin_jaar + 1, month=2, day=1)   # 1 februari
        begin_bk = date(year=comp.begin_jaar + 1, month=5, day=1)   # 1 mei

        comp.laatst_mogelijke_wedstrijd = begin_rk
        comp.rk_eerste_wedstrijd = begin_rk
        comp.rk_laatste_wedstrijd = begin_rk
        comp.bk_eerste_wedstrijd = begin_bk
        comp.bk_laatste_wedstrijd = begin_bk
        comp.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0014_aantal_scores'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='competitie',
            name='bk_eerste_wedstrijd',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='competitie',
            name='bk_laatste_wedstrijd',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='competitie',
            name='alle_regiocompetities_afgesloten',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitie',
            name='alle_rks_afgesloten',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitie',
            name='alle_bks_afgesloten',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='competitie',
            name='laatst_mogelijke_wedstrijd',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='competitie',
            name='rk_eerste_wedstrijd',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='competitie',
            name='rk_laatste_wedstrijd',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
        migrations.RunPython(initialiseer_nieuwe_datums),
    ]

# end of file
