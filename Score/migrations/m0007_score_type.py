# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def zet_score_type(apps, _):
    """ default: type='S'
        is_ag --> type='I' (automatisch vastgesteld) of 'T' (handmatig ingevoerd)
    """

    score_klas = apps.get_model('Score', 'Score')
    scorehist_klas = apps.get_model('Score', 'ScoreHist')

    # zet alle handmatig ingevoerde AG's op type=Team-AG
    for hist in (scorehist_klas                             # pragma: no cover
                 .objects
                 .select_related('score')
                 .filter(score__is_ag=True)
                 .exclude(door_account=None)):

        score = hist.score
        score.type = 'T'
        score.save(update_fields=['type'])
    # for

    for score in score_klas.objects.filter(is_ag=True):     # pragma: no cover
        if score.type != 'T':
            score.type = 'I'
            score.save(update_fields=['type'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0006_protect_schutterboog_delete'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='score',
            name='type',
            field=models.CharField(choices=[('S', 'Score'), ('I', 'Indiv AG'), ('T', 'Team AG')], default='S', max_length=1),
        ),
        migrations.RunPython(zet_score_type)
    ]

# end of file
