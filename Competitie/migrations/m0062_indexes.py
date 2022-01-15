# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0061_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['aantal_scores'], name='Competitie__aantal__1682db_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['aantal_scores', 'deelcompetitie'], name='Competitie__aantal__409f0d_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_83a773_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_2899dc_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_791c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['rank'], name='Competitie__rank_2f6fbf_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['volgorde', '-gemiddelde'], name='Competitie__volgord_9cc75f_idx'),
        ),
    ]

# end of file
